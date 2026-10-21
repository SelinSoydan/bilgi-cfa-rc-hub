"""Bilgi CFA RC Hub on Streamlit.

The screen is the same page as the claude.ai hub (frontend/index.html, built by
tools/build_frontend.py), so both look identical. Python keeps the data:
it sends everything to the page and saves every change the page sends back.
"""
import hashlib
import os

import streamlit as st
import streamlit.components.v1 as components

from hub.store import make_store

HERE = os.path.dirname(os.path.abspath(__file__))
st.set_page_config(page_title="Bilgi CFA RC Hub", page_icon="🟥", layout="wide", initial_sidebar_state="collapsed")
st.html("""<style>
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], footer { display:none !important; }
.block-container, [data-testid="stMainBlockContainer"] { padding:0 !important; max-width:100% !important; }
[data-testid="stMain"], [data-testid="stAppViewContainer"] { padding:0 !important; }
[data-testid="stVerticalBlock"] { gap:0 !important; }
iframe { display:block; border:0; }
.stApp { background:#ffffff; }
[data-stale="true"], .stale-element { opacity:1 !important; transition:none !important; filter:none !important; }
[data-testid="stStatusWidget"] { display:none !important; }
</style>""")


def _secret(name):
    try:
        return st.secrets.get(name)
    except Exception:
        return None


pw = _secret("app_password")
if pw and not st.session_state.get("ok"):
    st.markdown("<div style='max-width:420px;margin:12vh auto 0;padding:0 16px'>", unsafe_allow_html=True)
    st.title("Bilgi CFA RC Hub")
    st.caption("Team only. Ask Selin for the password.")
    if st.text_input("Password", type="password") == pw:
        st.session_state.ok = True
        st.rerun()
    st.stop()


with open(os.path.join(HERE, "seed.json"), "rb") as _f:
    SEED_HASH = hashlib.md5(_f.read()).hexdigest()


@st.cache_resource
def _store(seed_hash):
    return make_store(st.secrets if _secret("supabase") else {})


def store():
    return _store(SEED_HASH)


@st.cache_data(ttl=15, show_spinner=False)
def load():
    return store().all()


def public(data):
    return {col: {i: {k: v for k, v in d.items() if k not in ("id", "_v")} for i, d in docs.items()} for col, docs in data.items()}


HUB = components.declare_component("rc_hub", path=os.path.join(HERE, "frontend"))
DEMO = ("Demo mode: the shared database is not connected yet, so changes here can be lost when the app restarts. "
        "Keep real work in the claude.ai hub until it is connected.")


@st.fragment(run_every="30s")
def hub():
    done = st.session_state.setdefault("done", [])
    demo = DEMO if (store().name == "local SQLite" and os.path.exists("/mount/src")) else ""
    value = HUB(data=public(load()), acked=done[-300:], demo=demo, key="hub", default=None)
    fresh = [o for o in ((value or {}).get("ops") or []) if o.get("opid") not in done]
    if not fresh:
        return
    for o in fresh:
        try:
            if o["kind"] == "set":
                store().put(o["col"], o["id"], o.get("data") or {})
            elif o["kind"] == "update":
                store().patch(o["col"], o["id"], o.get("data") or {})
            elif o["kind"] == "delete":
                store().delete(o["col"], o["id"])
        except Exception as ex:  # shown to the user, never silent
            st.toast(f"Not saved: {ex}", icon="⚠️")
        done.append(o["opid"])
    load.clear()
    st.rerun(scope="fragment")


hub()
