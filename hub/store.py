"""Shared storage for the team hub.

One table of JSON documents, addressed by (collection, id), with a version
number so two people editing at once never overwrite each other silently.

Locally the table lives in SQLite (data/hub.db). In the cloud the same table
lives in Supabase (Postgres), reached through its REST API with `requests`,
so no database driver is needed. The backend is picked from st.secrets.
"""
import hashlib
import json
import os
import sqlite3
import time

import requests

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _clean(data):
    return {k: v for k, v in data.items() if k not in ("id", "_v")}


class SQLiteStore:
    name = "local SQLite"

    def __init__(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        with self._conn() as c:
            c.execute(
                "CREATE TABLE IF NOT EXISTS rc_docs ("
                "collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, "
                "version INTEGER NOT NULL DEFAULT 1, updated_at REAL, "
                "PRIMARY KEY (collection, id))"
            )

    def _conn(self):
        return sqlite3.connect(self.path, timeout=10)

    def all(self):
        with self._conn() as c:
            rows = c.execute("SELECT collection, id, data, version FROM rc_docs").fetchall()
        out = {}
        for col, doc_id, data, version in rows:
            d = json.loads(data)
            d["id"], d["_v"] = doc_id, version
            out.setdefault(col, {})[doc_id] = d
        return out

    def put(self, col, doc_id, data):
        body = json.dumps(_clean(data), ensure_ascii=False)
        with self._conn() as c:
            c.execute(
                "INSERT INTO rc_docs (collection, id, data, version, updated_at) VALUES (?, ?, ?, 1, ?) "
                "ON CONFLICT (collection, id) DO UPDATE SET data = excluded.data, "
                "version = rc_docs.version + 1, updated_at = excluded.updated_at",
                (col, doc_id, body, time.time()),
            )

    def patch(self, col, doc_id, fields):
        for _ in range(4):
            with self._conn() as c:
                row = c.execute(
                    "SELECT data, version FROM rc_docs WHERE collection = ? AND id = ?", (col, doc_id)
                ).fetchone()
                if not row:
                    raise KeyError(doc_id)
                d = json.loads(row[0])
                d.update(_clean(fields))
                cur = c.execute(
                    "UPDATE rc_docs SET data = ?, version = version + 1, updated_at = ? "
                    "WHERE collection = ? AND id = ? AND version = ?",
                    (json.dumps(d, ensure_ascii=False), time.time(), col, doc_id, row[1]),
                )
                if cur.rowcount == 1:
                    return
            time.sleep(0.05)
        raise RuntimeError("Someone else is editing this. Try again.")

    def delete(self, col, doc_id):
        with self._conn() as c:
            c.execute("DELETE FROM rc_docs WHERE collection = ? AND id = ?", (col, doc_id))

    def count(self):
        with self._conn() as c:
            return c.execute("SELECT COUNT(*) FROM rc_docs").fetchone()[0]


class SupabaseStore:
    """Same interface, over Supabase's REST API. Table: see supabase.sql."""

    name = "Supabase"

    def __init__(self, url, key, table="rc_docs"):
        self.base = url.rstrip("/") + "/rest/v1/" + table
        self.h = {"apikey": key, "Authorization": "Bearer " + key, "Content-Type": "application/json"}

    def _get(self, col, doc_id):
        r = requests.get(self.base, headers=self.h, timeout=15,
                         params={"select": "data,version", "collection": "eq." + col, "id": "eq." + doc_id})
        r.raise_for_status()
        rows = r.json()
        return rows[0] if rows else None

    def all(self):
        r = requests.get(self.base, headers=self.h, timeout=15, params={"select": "collection,id,data,version"})
        r.raise_for_status()
        out = {}
        for row in r.json():
            d = dict(row["data"] or {})
            d["id"], d["_v"] = row["id"], row["version"]
            out.setdefault(row["collection"], {})[row["id"]] = d
        return out

    def put(self, col, doc_id, data):
        cur = self._get(col, doc_id)
        body = {"collection": col, "id": doc_id, "data": _clean(data), "version": (cur["version"] + 1) if cur else 1}
        r = requests.post(self.base, headers=dict(self.h, Prefer="resolution=merge-duplicates"), json=body, timeout=15)
        r.raise_for_status()

    def patch(self, col, doc_id, fields):
        for _ in range(4):
            cur = self._get(col, doc_id)
            if not cur:
                raise KeyError(doc_id)
            d = dict(cur["data"] or {})
            d.update(_clean(fields))
            r = requests.patch(
                self.base, headers=dict(self.h, Prefer="return=representation"), timeout=15,
                params={"collection": "eq." + col, "id": "eq." + doc_id, "version": "eq." + str(cur["version"])},
                json={"data": d, "version": cur["version"] + 1},
            )
            r.raise_for_status()
            if r.json():
                return
            time.sleep(0.1)
        raise RuntimeError("Someone else is editing this. Try again.")

    def delete(self, col, doc_id):
        r = requests.delete(self.base, headers=self.h, timeout=15,
                            params={"collection": "eq." + col, "id": "eq." + doc_id})
        r.raise_for_status()

    def count(self):
        r = requests.get(self.base, headers=dict(self.h, Prefer="count=exact"), timeout=15,
                         params={"select": "id", "limit": "1"})
        r.raise_for_status()
        rng = r.headers.get("Content-Range", "*/0")
        return int(rng.split("/")[-1] or 0)


def make_store(secrets):
    sb = None
    try:
        sb = secrets.get("supabase")
    except Exception:
        sb = None
    store = SupabaseStore(sb["url"], sb["key"]) if sb else SQLiteStore(os.path.join(HERE, "data", "hub.db"))
    seed_path = os.path.join(HERE, "seed.json")
    if not os.path.exists(seed_path):
        return store
    with open(seed_path, "rb") as f:
        raw = f.read()
    digest = hashlib.md5(raw).hexdigest()
    empty = store.count() == 0
    # The local/demo SQLite copy follows seed.json whenever it changes.
    # A real shared database (Supabase) is only seeded once, never overwritten.
    stale = isinstance(store, SQLiteStore) and (store.all().get("meta", {}).get("_seed", {}) or {}).get("hash") != digest
    if empty or stale:
        for col, docs in json.loads(raw.decode("utf-8")).items():
            for doc_id, data in docs.items():
                store.put(col, doc_id, data)
        store.put("meta", "_seed", {"hash": digest})
    return store
