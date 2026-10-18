"""Bilgi RC Hub: the team app for the CFA Institute Research Challenge 2026-27 (Borusan Pipe).

Run locally:   streamlit run app.py
Cloud setup:   see DEPLOY.md
"""
import datetime as dt
import os
import time
import uuid

import streamlit as st

from hub.content import (COLS, DOC, DOCS, MAP, NKIND, PHASES, PRES, QUESTION_ORDER, REPORT_ORDER, ROAD, ROLES,
                         SECTIONS, WIP, ZONES, COLORS)
from hub.store import make_store
from hub.ui import (av, by_due, color, current_sprint_id, days, e, fd, has, in_sprint, inject_css, is_mine, label,
                    member, members, owners, role_name, sprints_sorted, steps_bar, steps_info, today)

st.set_page_config(page_title="Bilgi CFA RC Hub", page_icon="🟥", layout="wide", initial_sidebar_state="collapsed")
inject_css()


# ---------------------------------------------------------------- access + data
def _secret(name):
    try:
        return st.secrets.get(name)
    except Exception:
        return None


def gate():
    pw = _secret("app_password")
    if not pw or st.session_state.get("ok"):
        return
    st.title("Bilgi CFA RC Hub")
    st.caption("Team only. Ask Selin for the password.")
    if st.text_input("Password", type="password") == pw:
        st.session_state.ok = True
        st.rerun()
    st.stop()


gate()


@st.cache_resource
def store():
    return make_store(st.secrets if _secret("supabase") else {})


@st.cache_data(ttl=20, show_spinner=False)
def load():
    return store().all()


def D():
    return load()


def write(fn, *args, ok=None):
    try:
        fn(*args)
    except Exception as ex:  # shown to the user, never silent
        st.toast(f"Not saved: {ex}", icon="⚠️")
        return False
    load.clear()
    if ok:
        st.toast(ok)
    return True


def tasks(data, include_deleted=False):
    return [t for t in (data.get("tasks") or {}).values() if include_deleted or not t.get("deleted")]


def notes(data, include_deleted=False):
    return [n for n in (data.get("notes") or {}).values() if include_deleted or not n.get("deleted")]


# ---------------------------------------------------------------- dialogs
@st.dialog("Task", width="large")
def task_dialog(tid=None):
    data = D()
    t = dict((data.get("tasks") or {}).get(tid, {})) if tid else {}
    sp = st.session_state.get("sp", "backlog")
    if not tid:
        t = {"status": "todo", "assignees": [], "sprint": "" if sp == "backlog" else sp}
    skey = f"steps_{tid or 'new'}"
    if skey not in st.session_state:
        st.session_state[skey] = [dict(x) for x in (t.get("steps") or [])]
    steps = st.session_state[skey]

    title = st.text_input("What needs to be done?", value=t.get("title", ""), placeholder="e.g. Find 5 years of revenue in USD")
    people = [m["id"] for m in members(data)] + ["all"]
    cur = [x for x in (t.get("assignees") or ([t["owner"]] if t.get("owner") else [])) if x in people]
    who = st.multiselect("Who (two people can share a task)", people, default=cur, format_func=lambda x: label(data, x))
    if t.get("role") and not who:
        st.caption(f"Nobody picked: it goes to whoever has the {role_name(t['role'])} role.")
    status = st.segmented_control("Status", [c[0] for c in COLS], default=t.get("status", "todo"),
                                  format_func=lambda k: dict((c[0], c[1]) for c in COLS)[k])

    st.markdown("**Checklist**")
    for i, s in enumerate(steps):
        row = st.container(horizontal=True, vertical_alignment="center")
        s["d"] = row.checkbox(s["t"], value=s.get("d", False), key=f"{skey}_{i}_{s['t'][:20]}")
        if row.button("✕", key=f"{skey}_x{i}", type="tertiary", help="Remove this step"):
            steps.pop(i)
            st.rerun(scope="fragment")
    add = st.container(horizontal=True, vertical_alignment="bottom")
    new_step = add.text_input("Add a step", key=f"{skey}_new", label_visibility="collapsed", placeholder="Add a step")
    if add.button("Add", key=f"{skey}_add") and new_step.strip():
        steps.append({"t": new_step.strip(), "d": False})
        st.rerun(scope="fragment")

    sps = sprints_sorted(data)
    sp_ids = [s["id"] for s in sps] + [""]
    c1, c2, c3 = st.columns(3)
    sprint = c1.selectbox("Sprint", sp_ids, index=sp_ids.index(t.get("sprint")) if t.get("sprint") in sp_ids else len(sp_ids) - 1,
                          format_func=lambda x: next((s["name"] for s in sps if s["id"] == x), "Backlog"))
    due = c2.date_input("Due (optional)", value=dt.date.fromisoformat(t["due"]) if t.get("due") else None, format="DD/MM/YYYY")
    ph_keys = [""] + list(PHASES)
    phase = c3.selectbox("Map step", ph_keys, index=ph_keys.index(t.get("phase", "")) if t.get("phase", "") in ph_keys else 0,
                         format_func=lambda k: PHASES.get(k, "None"))

    b = st.container(horizontal=True)
    if b.button("Save", type="primary"):
        if not title.strip():
            st.warning("Write the task first.")
            return
        doc = {"title": title.strip(), "assignees": who, "status": status or "todo", "sprint": sprint,
               "due": due.isoformat() if due else "", "phase": phase, "steps": steps, "updated": int(time.time() * 1000)}
        if tid:
            ok = write(store().patch, "tasks", tid, doc, ok="Saved")
        else:
            doc.update({"role": "", "created": int(time.time() * 1000)})
            ok = write(store().put, "tasks", "t" + uuid.uuid4().hex[:10], doc, ok="Task added")
        if ok:
            st.session_state.pop(skey, None)
            st.rerun()
    if tid and b.button("Move to trash", type="tertiary", help="You can bring it back from Trash"):
        if write(store().patch, "tasks", tid, {"deleted": True}, ok="Moved to trash. Undo it in Trash."):
            st.session_state.pop(skey, None)
            st.rerun()


@st.dialog("Note", width="large")
def note_dialog(nid=None):
    data = D()
    n = dict((data.get("notes") or {}).get(nid, {})) if nid else {"kind": "note", "date": today()}
    kind = st.segmented_control("Type", list(NKIND), default=n.get("kind", "note"), format_func=lambda k: NKIND[k][0])
    title = st.text_input("Title", value=n.get("title", ""), placeholder="e.g. Margin fell in 2024 because energy pipe prices dropped")
    hours, with_ = 0.0, n.get("with", "advisor")
    if kind == "help":
        c1, c2 = st.columns(2)
        with_ = c1.segmented_control("With", ["advisor", "mentor"], default=with_,
                                     format_func=lambda k: {"advisor": "Faculty advisor", "mentor": "Industry mentor"}[k])
        hours = c2.number_input("Hours", min_value=0.0, step=0.25, value=float(n.get("hours") or 0))
    body = st.text_area("Text", value=n.get("body", ""), height=140,
                        placeholder="Insight: what it means for Borusan, with document, page and line. AI use: tool, what for, how we checked it.")
    link = st.text_input("Source link", value=n.get("link", ""), placeholder="https://")
    c1, c2 = st.columns(2)
    ids = [""] + [m["id"] for m in members(data)]
    author = c1.selectbox("Who", ids, index=ids.index(n.get("author", "")) if n.get("author", "") in ids else 0,
                          format_func=lambda x: label(data, x) if x else "Team")
    date = c2.date_input("Date", value=dt.date.fromisoformat(n["date"]) if n.get("date") else dt.date.today(), format="DD/MM/YYYY")
    b = st.container(horizontal=True)
    if b.button("Save", type="primary"):
        if not title.strip():
            st.warning("Give it a title.")
            return
        if kind == "help" and not hours:
            st.warning("Add the hours.")
            return
        doc = {"kind": kind or "note", "title": title.strip(), "body": body, "link": link, "author": author,
               "date": date.isoformat(), "updated": int(time.time() * 1000)}
        if kind == "help":
            doc.update({"with": with_ or "advisor", "hours": hours})
        if nid:
            ok = write(store().patch, "notes", nid, doc, ok="Saved")
        else:
            doc["created"] = int(time.time() * 1000)
            ok = write(store().put, "notes", "n" + uuid.uuid4().hex[:10], doc, ok="Note added")
        if ok:
            st.rerun()
    if nid and b.button("Move to trash", type="tertiary"):
        if write(store().patch, "notes", nid, {"deleted": True}, ok="Moved to trash"):
            st.rerun()


@st.dialog("Sprint")
def sprint_dialog(sid=None):
    data = D()
    s = dict((data.get("sprints") or {}).get(sid, {})) if sid else {}
    name = st.text_input("Name", value=s.get("name", f"Sprint {len(data.get('sprints') or {}) + 1}"))
    c1, c2 = st.columns(2)
    start = c1.date_input("Start", value=dt.date.fromisoformat(s["start"]) if s.get("start") else dt.date.today(), format="DD/MM/YYYY")
    end = c2.date_input("End", value=dt.date.fromisoformat(s["end"]) if s.get("end") else dt.date.today() + dt.timedelta(days=6), format="DD/MM/YYYY")
    goal = st.text_input("Goal (one sentence)", value=s.get("goal", ""))
    if st.button("Save", type="primary"):
        if end < start:
            st.warning("End is before start.")
            return
        new_id = sid or "s" + uuid.uuid4().hex[:8]
        if write(store().put, "sprints", new_id, {"name": name, "start": start.isoformat(), "end": end.isoformat(), "goal": goal}, ok="Saved"):
            st.session_state.sp = new_id
            st.rerun()


@st.dialog("Names, roles and colours", width="large")
def team_dialog():
    data = D()
    if "team_draft" not in st.session_state:
        st.session_state.team_draft = [dict(m) for m in members(data)]
    draft = st.session_state.team_draft
    st.caption('A role means "writes the first draft". Role tasks follow the person automatically.')
    role_keys = [""] + list(ROLES)
    for i, m in enumerate(draft):
        c0, c1, c2, c3 = st.columns([1, 3, 3, 1], vertical_alignment="bottom")
        m["color"] = c0.color_picker("Colour", value=m.get("color") or COLORS[i % len(COLORS)], key=f"tc{i}", label_visibility="collapsed")
        m["name"] = c1.text_input("Name", value=m.get("name", ""), key=f"tn{i}")
        m["role"] = c2.selectbox("Role", role_keys, index=role_keys.index(m.get("role", "")) if m.get("role", "") in role_keys else 0,
                                 key=f"tr{i}", format_func=lambda k: role_name(k) or "No role yet")
        if c3.button("✕", key=f"tx{i}", help="Remove"):
            draft.pop(i)
            st.rerun(scope="fragment")
    if st.button("+ Add person"):
        draft.append({"id": "m" + uuid.uuid4().hex[:6], "name": "", "role": "", "color": COLORS[len(draft) % len(COLORS)]})
        st.rerun(scope="fragment")
    if st.button("Save", type="primary"):
        clean = [{"id": m["id"], "name": m["name"].strip(), "role": m.get("role", ""), "color": m.get("color", "")} for m in draft if m.get("name", "").strip()]
        if write(store().put, "meta", "team", {"members": clean, "updated": int(time.time() * 1000)}, ok="Team saved"):
            st.session_state.pop("team_draft", None)
            st.rerun()


@st.dialog("Key dates")
def dates_dialog():
    data = D()
    ev = [dict(x) for x in (data.get("meta", {}).get("dates", {}) or {}).get("events", [])]
    for i, x in enumerate(ev):
        c1, c2 = st.columns(2)
        x["name"] = c1.text_input("Name", value=x.get("name", ""), key=f"en{i}")
        d = c2.date_input("Date", value=dt.date.fromisoformat(x["date"]) if x.get("date") else None, key=f"ed{i}", format="DD/MM/YYYY")
        x["date"] = d.isoformat() if d else None
    if st.button("Save", type="primary"):
        if write(store().put, "meta", "dates", {"events": ev, "updated": int(time.time() * 1000)}, ok="Dates saved"):
            st.rerun()


@st.dialog("Shared folder")
def folder_dialog():
    data = D()
    url = st.text_input("Link to our Drive or OneDrive folder", value=(data.get("meta", {}).get("links", {}) or {}).get("folder", ""), placeholder="https://")
    if st.button("Save", type="primary"):
        if url and not url.startswith("http"):
            st.warning("Use a full https:// link.")
            return
        if write(store().put, "meta", "links", {"folder": url, "updated": int(time.time() * 1000)}, ok="Saved"):
            st.rerun()


# ---------------------------------------------------------------- pieces
def move(tid, to):
    write(store().patch, "tasks", tid, {"status": to, "updated": int(time.time() * 1000)},
          ok="Done ✓ Ask someone to check it." if to == "done" else None)


def countdown(data):
    ev = (data.get("meta", {}).get("dates", {}) or {}).get("events", []) or [{"name": "Kickoff", "date": "2026-11-09"}]
    nxt = next((i for i, x in enumerate(ev) if x.get("date") and days(x["date"]) >= 0), -1)
    tiles = []
    for i, x in enumerate(ev):
        if x.get("date"):
            n = days(x["date"])
            big, unit = (n, "day" if n == 1 else "days") if n > 0 else (("Today", "") if n == 0 else ("✓", ""))
        else:
            parts = (x.get("label") or "?").split(" ")
            big, unit = parts[0], " ".join(parts[1:])
        sub = fd(x["date"]) if x.get("date") else "date to confirm"
        tiles.append(f'<div class="rc-tile{" next" if i == nxt else ""}"><span class="n">{e(big)}</span><span class="u">{e(unit)}</span>'
                     f'<div class="w">{e(x.get("name"))}</div><div class="d">{e(sub)}</div></div>')
    st.html(f'<div class="rc-count">{"".join(tiles)}</div>')


def card(data, t, status):
    o = owners(data, t)
    tag = (f'<span class="rc-ph">{e(PHASES[t["phase"]])}</span>' if t.get("phase") in PHASES
           else (f'<span class="rc-ph role">{e(role_name(t["role"]))}</span>' if t.get("role") in ROLES else ""))
    late = t.get("due") and status != "done" and days(t["due"]) < 0
    bits = " · ".join(x for x in [steps_info(t), (f'<span class="{"rc-late" if late else ""}">{"late, " if late else ""}{e(fd(t["due"]))}</span>' if t.get("due") else "")] if x)
    who = ('<span class="rc-stack">' + "".join(av(data, x) for x in o) + "</span>") if o else av(data, "")
    with st.container(border=True, key=f"card_{t['id']}"):
        st.html(f'{tag}<div class="rc-t{" done" if status == "done" else ""}" title="{e(t.get("title"))}">{e(t.get("title"))}</div>'
                f'<div class="rc-m">{bits}</div>{steps_bar(t)}<div>{who}</div>')
        row = st.container(horizontal=True, gap="small", key=f"row_{t['id']}")
        if row.button("Open", key=f"o_{t['id']}", help="Open the task"):
            task_dialog(t["id"])
        nxt = {"todo": ("Start", "doing"), "doing": ("Done ✓", "done"), "done": ("↺", "doing")}[status]
        if row.button(nxt[0], key=f"g_{t['id']}"):
            move(t["id"], nxt[1])
            st.rerun()


# ---------------------------------------------------------------- pages
def page_board():
    data = D()
    top = st.container(horizontal=True, vertical_alignment="center")
    top.markdown('<span class="rc-sub">CFA Research Challenge 2026-27 · Borusan Pipe</span>', unsafe_allow_html=True)
    if top.button("Edit dates", type="tertiary"):
        dates_dialog()
    countdown(data)

    sps = sprints_sorted(data)
    views = [s["id"] for s in sps] + ["backlog"]
    if st.session_state.get("sp") not in views:
        st.session_state.sp = current_sprint_id(data)
    i = views.index(st.session_state.sp)
    s = next((x for x in sps if x["id"] == st.session_state.sp), None)
    lst = [t for t in tasks(data) if in_sprint(data, t, st.session_state.sp)]
    done = sum(1 for t in lst if t.get("status") == "done")

    with st.container(border=True):
        h = st.container(horizontal=True, vertical_alignment="center")
        if h.button("‹", disabled=i <= 0, key="prev"):
            st.session_state.sp = views[i - 1]
            st.rerun()
        h.markdown(f"**{e(s['name']) if s else 'Backlog'}** &nbsp; <span class='rc-sub'>{fd(s['start']) + ' to ' + fd(s['end']) if s else 'Later, not in a sprint yet'}</span>", unsafe_allow_html=True)
        if s and h.button("Edit", type="tertiary", key="edit_sp"):
            sprint_dialog(s["id"])
        if h.button("+ Sprint", type="tertiary", key="new_sp"):
            sprint_dialog(None)
        if h.button("›", disabled=i >= len(views) - 1, key="next"):
            st.session_state.sp = views[i + 1]
            st.rerun()
        if s and s.get("goal"):
            st.markdown(f"<span style='color:#b0182d;font-weight:800'>Goal</span> {e(s['goal'])}", unsafe_allow_html=True)
        left = ""
        if s:
            n = days(s["end"])
            left = f" · {n} day{'s' if n != 1 else ''} left" if n > 0 else (" · last day" if n == 0 else " · finished")
        st.progress(done / len(lst) if lst else 0.0, text=f"{done} of {len(lst)} done{left}")
        ids = [m["id"] for m in members(data)]
        if any(has(data, t, "all") for t in lst):
            ids.append("all")
        if any(not owners(data, t) for t in lst):
            ids.append("")

        def fmt(x):
            mine = [t for t in lst if has(data, t, x)]
            d = sum(1 for t in mine if t.get("status") == "done")
            doing = sum(1 for t in mine if t.get("status") == "doing")
            tail = "no tasks" if not mine else ("all done ✓" if d == len(mine) else f"{d}/{len(mine)}")
            return f"{label(data, x)} · {tail}" + (" ⚠" if doing > WIP else "")
        who = st.pills("Show only", ids, format_func=fmt, key="who", label_visibility="collapsed")

    bar = st.container(horizontal=True, vertical_alignment="center")
    bar.caption("Tap a name above to see only their tasks. Two people can share a task. Max 2 in Doing per person.")
    if bar.button("+ New task", type="primary"):
        task_dialog(None)

    shown = sorted([t for t in lst if who is None or has(data, t, who)], key=by_due)
    cols = st.columns(3, gap="small")
    for col, (k, name, c) in zip(cols, COLS):
        mine = [t for t in shown if (t.get("status") or "todo") == k]
        with col:
            st.html(f'<div class="rc-colh"><span class="dot" style="background:{c}"></span>{name}<span class="c">{len(mine)}</span></div>')
            if not mine:
                st.caption({"todo": "Nothing here", "doing": "Nothing in progress", "done": "Nothing done yet"}[k])
            grid = st.columns(2, gap="small")
            for j, t in enumerate(mine):
                with grid[j % 2]:
                    card(data, t, k)
    st.caption("Done means someone else checked it · Monday: update your cards")


def page_team():
    data = D()
    if st.session_state.get("person"):
        return person_view(data, st.session_state.person)
    h = st.container(horizontal=True, vertical_alignment="center")
    h.title("Team")
    folder = (data.get("meta", {}).get("links", {}) or {}).get("folder", "")
    if folder.startswith("http"):
        h.link_button("Shared folder ↗", folder)
    if h.button("Edit folder link" if folder else "+ Link shared folder", type="tertiary"):
        folder_dialog()
    st.html('<div class="rc-box" style="background:#18191d;color:#f4f2ef"><b style="color:#ff8c9c">Everyone learns everything.</b> '
            "A role only says who writes the first draft of a section. All of us read the same documents, check each other's numbers, and can answer any judge question.</div>")
    ms = members(data)
    grid = st.columns(3)
    for i, m in enumerate(ms):
        mine = [t for t in tasks(data) if has(data, t, m["id"])]
        d = sum(1 for t in mine if t.get("status") == "done")
        with grid[i % 3]:
            with st.container(border=True):
                st.html(f'<div style="display:flex;gap:12px;align-items:center">{av(data, m["id"], 44)}<div><b style="font-size:17px">{e(m.get("name"))}</b>'
                        f'<div class="rc-sub">{e(role_name(m.get("role")) or "Role not set yet")} · {d}/{len(mine)} tasks done</div></div></div>')
                if st.button("Open page", key=f"p_{m['id']}", type="tertiary"):
                    st.session_state.person = m["id"]
                    st.rerun()
    if st.button("Edit names, roles and colours"):
        st.session_state.pop("team_draft", None)
        team_dialog()


def person_view(data, mid):
    m = member(data, mid)
    if st.button("‹ Team", type="tertiary"):
        st.session_state.person = None
        st.rerun()
    if not m:
        st.info("Person not found.")
        return
    r = ROLES.get(m.get("role", ""))
    mine = sorted([t for t in tasks(data) if is_mine(data, t, mid)], key=by_due)
    open_ = [t for t in mine if t.get("status") != "done"]
    st.html(f'<div style="display:flex;gap:14px;align-items:center">{av(data, mid, 56)}<div><h1 style="margin:0">{e(m.get("name"))}</h1>'
            f'<div class="rc-sub">{e(r[0]) + " (first draft)" if r else "Role not set yet"} · {len(mine) - len(open_)} of {len(mine)} tasks done</div></div></div>')
    cur = current_sprint_id(data)
    st.subheader("This sprint")
    now = [t for t in open_ if t.get("sprint") == cur]
    for t in now or []:
        task_row(data, t)
    if not now:
        st.caption("Nothing open in this sprint.")
    st.subheader("Your part")
    if r:
        st.write(r[2])
        for k in r[1]:
            sec = SECTIONS[k]
            st.markdown(f"**{sec[0]}** ({sec[1]} points): {sec[3]}")
    else:
        st.write("No role yet. Until we pick roles, everyone starts with the same three documents below.")
    st.subheader("Read first")
    doc_cards([DOC[k] for k in (r[3] if r else ["pres2q26", "ar2025", "guidance"])])
    st.subheader("All your open tasks")
    for t in open_:
        task_row(data, t)
    if not open_:
        st.caption("All done ✓")


def task_row(data, t):
    with st.container(border=True):
        c1, c2, c3 = st.columns([6, 1, 1], vertical_alignment="center")
        sp = next((s["name"] for s in sprints_sorted(data) if s["id"] == t.get("sprint")), "Backlog")
        c1.html(f'<b>{e(t["title"])}</b><div class="rc-m">{sp}{" · " + fd(t["due"]) if t.get("due") else ""} {steps_info(t)}</div>')
        if c2.button("Open", key=f"to_{t['id']}", type="tertiary"):
            task_dialog(t["id"])
        k = t.get("status") or "todo"
        nxt = {"todo": ("Start", "doing"), "doing": ("Done ✓", "done"), "done": ("↺", "doing")}[k]
        if c3.button(nxt[0], key=f"tg_{t['id']}"):
            move(t["id"], nxt[1])
            st.rerun()


def doc_cards(docs):
    cols = st.columns(2)
    for i, d in enumerate(docs):
        g, did, title, date, url, what, look, use = d
        with cols[i % 2]:
            with st.container(border=True):
                st.html(f'<div style="display:flex;justify-content:space-between;gap:8px"><b>{e(title)}</b><span class="rc-sub">{e(date)}</span></div>'
                        f'<div class="rc-muted">{e(what)}</div><div style="font-size:14px;margin-top:4px">{e(look)}</div>'
                        f'<div style="margin-top:6px">{" ".join(f"<span class=rc-ph style=color:#676b74;background:#eeeae5>{e(SECTIONS[u][0])}</span>" for u in use)}</div>')
                st.link_button("Open ↗", url)


def page_learn():
    st.title("Where do we start?")
    st.markdown("Not with the DCF. A valuation is a story told in numbers, so we learn the story first. **The method comes last, because the business decides the method.**")
    steps = [
        ("The story", "Read the latest investor presentation, then the first part of the 2025 Annual Report.", "Done when each of us can say in three sentences what Borusan sells, who buys it, and where the money comes from."),
        ("The numbers", "Open the financial reports for 2023, 2024, 2025 and the latest quarter. Build one table in US dollars: sales volume, revenue, EBITDA, margin, debt, cash flow.", "Why dollars? The company gives its own guidance in dollars, so our numbers can be compared with it directly."),
        ("The industry", "Who are the peers, and what moves demand? Borusan sells into four areas: infrastructure and projects, industrial and construction, automotive and industrial uses, and energy.", "Ask why Borusan's margin is higher or lower than its peers: price, volume, cost, or location?"),
        ("The method", "Only now. Our main tool is a DCF of the whole firm, checked against peer multiples like EV/EBITDA.", "The DCF shows what the business is worth from its own cash. Multiples show what the market pays for similar businesses. If the two disagree a lot, one of our assumptions is wrong."),
    ]
    for i, (h, p, why) in enumerate(steps, 1):
        with st.container(border=True):
            st.markdown(f"### {i}. {h}")
            st.write(p)
            st.info(why)
    st.subheader("One question per report section")
    st.caption('We never collect data "just in case". Every piece of data answers one of these questions.')
    for k in QUESTION_ORDER:
        sec = SECTIONS[k]
        st.markdown(f"**{sec[0]}** · {sec[1]} points  \n{sec[3]}")
    st.subheader("Borusan's own numbers show a cycle")
    st.write("The EBITDA margin went from 18.2% in 2023 to 6.0% in 2024. Same company, very different year. Valued on its best year it looks cheap; on its worst year it looks expensive.")
    st.table({"": ["Volume (m tons)", "Revenue ($ bn)", "EBITDA margin"],
              "2021": ["0.76", "0.8", "9.8%"], "2022": ["0.85", "1.3", "14.9%"], "2023": ["1.06", "1.7", "18.2%"],
              "2024": ["1.17", "1.7", "6.0%"], "2025": ["1.31", "1.8", "7.4%"], "2026 guide": ["1.15-1.25", "2.2-2.4", "9-11%"]})
    st.caption("Source: Borusan Pipe, Guidance page (borusanpipe.com/investor-relations/guidance), rows Sales Volume, Revenue, EBITDA Margin; read 18 Oct 2026.")
    st.write("**What we do with it:** for cyclical companies, Damodaran uses the margin of a normal year instead of the latest year. Our first big question: what is a normal margin for Borusan, and why?")


def page_docs():
    st.title("Research and documents")
    st.write("Only primary sources: the company, the regulator, the filing itself. Every link opens the original document.")
    st.subheader("How to read a report in three passes")
    c = st.columns(3)
    c[0].info("**1. Skim, 10 minutes.** Contents, highlights, the CEO letter. Where is everything?")
    c[1].info("**2. Hunt.** Take one question from your section. Find the table that answers it.")
    c[2].info("**3. Write one insight.** One sentence plus the source (document, page, line) in Notes.")
    groups = []
    for d in DOCS:
        if d[0] not in groups:
            groups.append(d[0])
    for g in groups:
        st.subheader(g)
        if g == "The numbers":
            st.warning("Q3 2026 results arrive on 6 November, three days before the kickoff. We read them first, then ask sharper questions on 9 November.")
        doc_cards([d for d in DOCS if d[0] == g])


def page_rules():
    data = D()
    st.title("Rules and scoring")
    st.write("Report and presentation count 50% each. If two teams tie, financial analysis decides first, then valuation.")
    st.subheader("The report: 100 points")
    st.html('<div class="rc-score">' + "".join(f'<div style="flex:{SECTIONS[k][1]};background:{SECTIONS[k][2]}">{SECTIONS[k][1]}<span>{e(SECTIONS[k][0])}</span></div>' for k in REPORT_ORDER) + "</div>")
    st.subheader("The presentation: 100 points")
    st.html('<div class="rc-score">' + "".join(f'<div style="flex:{p[1]};background:{p[2]}">{p[1]}<span>{e(p[0])}</span></div>' for p in PRES) + "</div>")
    st.caption("Q&A is worth as much as valuation. Everyone must be able to answer any question.")
    st.subheader("Outside help used so far")
    tot = {"advisor": 0.0, "mentor": 0.0}
    for n in notes(data):
        if n.get("kind") == "help" and n.get("with") in tot:
            tot[n["with"]] += float(n.get("hours") or 0)
    c = st.columns(2)
    for col, (k, name, mx) in zip(c, [("advisor", "Faculty advisor (Faruk Hoca)", 10), ("mentor", "Industry mentor", 6)]):
        u = round(tot[k], 2)
        col.progress(min(1.0, u / mx), text=f"{name}: {u} of {mx} hours" + (" · limit reached" if u >= mx else ""))
    st.caption('Counted from Notes of type "Help hour". Add one after every mentor or advisor meeting.')
    st.subheader("What we must do")
    rules = [("📄", "10 + 10 pages", "Report in English, 10 pages plus up to 10 pages of appendix."),
             ("🌐", "Public information only", "Every number has a source: document, page, line."),
             ("🤖", "AI is allowed, if disclosed", "Appendix B: what we used, how we checked it, how it shaped our judgment. Log every use in Notes."),
             ("⏱️", "Limited outside help", "Industry mentor up to 6 hours, faculty advisor up to 10 hours."),
             ("🚫", "No other professionals", "No outside analysts and no professional mock juries."),
             ("🏢", "Company contact", "Only through the official process, like the kickoff Q&A."),
             ("✍️", "Our own work", "The report is written by the five of us.")]
    c = st.columns(3)
    for i, (ic, b, s) in enumerate(rules):
        with c[i % 3]:
            with st.container(border=True):
                st.markdown(f"{ic} **{b}**  \n{s}")


def page_notes():
    data = D()
    h = st.container(horizontal=True, vertical_alignment="center")
    h.title("Notes")
    if h.button("+ Add", type="primary"):
        note_dialog(None)
    st.caption("Insights with their source, meeting notes, kickoff questions, our AI log and help hours.")
    ns = notes(data)
    kind = st.pills("Type", ["all"] + list(NKIND), default="all", label_visibility="collapsed",
                    format_func=lambda k: ("All" if k == "all" else NKIND[k][0]) + f" · {len(ns) if k == 'all' else sum(1 for n in ns if n.get('kind') == k)}")
    lst = [n for n in ns if kind in (None, "all") or n.get("kind") == kind]
    lst.sort(key=lambda n: (not (n.get("kind") == "question" and n.get("star")), -(n.get("created") or 0)))
    cols = st.columns(2)
    for i, n in enumerate(lst):
        k = NKIND.get(n.get("kind"), NKIND["note"])
        with cols[i % 2]:
            with st.container(border=True):
                who = label(data, n["author"]) if n.get("author") else "Team"
                st.html(f'<span class="rc-ph" style="color:#fff;background:{k[1]}">{e(k[0])}</span>'
                        f'<div style="font-weight:800;margin-top:6px">{e(n.get("title"))}</div><div class="rc-sub">{e(who)}{" · " + fd(n["date"]) if n.get("date") else ""}</div>'
                        + (f'<div class="rc-sub"><b>{n.get("hours")} h</b> with {"industry mentor" if n.get("with") == "mentor" else "faculty advisor"}</div>' if n.get("kind") == "help" else "")
                        + (f'<div style="white-space:pre-wrap;font-size:14px;margin-top:6px">{e(n.get("body"))}</div>' if n.get("body") else ""))
                row = st.container(horizontal=True)
                if n.get("link", "").startswith("http"):
                    row.link_button("Source ↗", n["link"], type="tertiary")
                if n.get("kind") == "question":
                    if row.button("★ Shortlisted" if n.get("star") else "☆ Shortlist", key=f"s_{n['id']}", type="tertiary"):
                        write(store().patch, "notes", n["id"], {"star": not n.get("star")})
                        st.rerun()
                if row.button("Edit", key=f"e_{n['id']}", type="tertiary"):
                    note_dialog(n["id"])
    if not lst:
        st.caption("Nothing here yet. Add your first insight with its source.")


def page_map():
    data = D()
    st.title("The map: the CFA way and our way")
    st.write("The CFA curriculum describes valuation in five steps. Below: the road to CFA day, then each step with what we actually do for Borusan.")

    a, b = dt.date.fromisoformat(ROAD[0]), dt.date.fromisoformat(ROAD[1])

    def pct(iso):
        return max(0.0, min(100.0, (dt.date.fromisoformat(iso) - a).days / (b - a).days * 100))

    tp = pct(today())
    ev = (data.get("meta", {}).get("dates", {}) or {}).get("events", [])
    approx = {"Jan 2027": "2027-01-15", "Feb 2027": "2027-02-15"}
    stations = "".join(f'<div class="rc-station{" low" if j % 2 else ""}" style="left:{pct(x.get("date") or approx.get(x.get("label"), ROAD[1]))}%">{e(x.get("name"))}{"" if x.get("date") else " ?"}</div>' for j, x in enumerate(ev))
    zones = "".join(f'<div class="rc-zone" style="left:{pct(s)}%;width:{pct(en) - pct(s)}%;background:{c}"><span>{z}</span></div>' for z, s, en, c in ZONES)
    lanes = []
    all_t = tasks(data)
    for m in members(data) + [{"id": "all", "name": "Team"}]:
        mine = all_t if m["id"] == "all" else [t for t in all_t if is_mine(data, t, m["id"])]
        p = (sum(1 for t in mine if t.get("status") == "done") / len(mine) * 100) if mine else 0
        lanes.append(f'<div class="rc-lane"><b style="font-size:13px">{e(m["name"])}</b><div class="rc-rail"><div class="tl" style="left:{tp}%"></div>'
                     f'<span class="rc-av" style="left:{p}%;{"background:#18191d;color:#FFE600" if m["id"] == "all" else "background:" + color(data, m["id"])}">{e("★" if m["id"] == "all" else m["name"][:1])}</span></div>'
                     f'<b style="font-size:12px;color:{"#2b7655" if p >= tp else "#a2660b"}">{p:.0f}%</b></div>')
    with st.container(border=True):
        st.markdown("**Road to CFA day** · Your dot moves as you finish tasks. Stay ahead of the red line.")
        st.html(f'<div class="rc-track">{zones}{stations}<div class="rc-today" style="left:{tp}%"><b>Today</b></div></div>{"".join(lanes)}')

    st.subheader("Five steps")
    t0 = today()
    for m in MAP:
        parts = ""
        if m.get("parts"):
            now_set, cells = False, []
            for p in m["parts"]:
                ts = [t for t in all_t if t.get("phase") == p["id"]]
                d = sum(1 for t in ts if t.get("status") == "done")
                full = ts and d == len(ts)
                is_now = (not full) and (not now_set) and t0 <= p["e"]
                now_set = now_set or is_now
                badge = '<span class="badge done">Done</span>' if full else (f'<span class="badge">{"Now" if t0 >= p["s"] else "Next"}</span>' if is_now else "")
                items = "".join(f'<li>{"✓" if t.get("status") == "done" else ("◐" if t.get("status") == "doing" else "○")} {e(t["title"])}</li>' for t in ts)
                count = (f"{d} of {len(ts)} {'task' if len(ts) == 1 else 'tasks'} done") if ts else "No tasks yet"
                cells.append(f'<div class="rc-part{" now" if is_now else ""}"><div class="pn">{e(p["id"])} {e(p["t"])} {badge}</div>'
                             f'<div class="rc-muted" style="font-size:13px">{e(p["cfa"])}</div><div style="margin-top:4px"><b>What we do:</b> {e(p["ours"])}</div>'
                             f'<div class="rc-sub" style="margin-top:4px">{fd(p["s"])} to {fd(p["e"])} · {count}</div><ul>{items}</ul></div>')
            parts = f'<div class="rc-parts">{"".join(cells)}</div>'
        st.html(f'<div class="rc-mstep"><div class="h"><span class="n">{m["n"]}</span><b>{e(m["t"])}</b><span class="w">{e(m["when"])} · {e(m["secs"])}</span></div>'
                f'<div class="c"><div><div class="rc-k" style="color:#676b74">The CFA way</div>{e(m["cfa"])}</div>'
                f'<div><div class="rc-k">Our way for Borusan</div>{e(m["ours"])}<div class="rc-sub" style="margin-top:6px"><b>We are done when:</b> {e(m["out"])}</div></div></div>{parts}</div>')

    st.subheader("Proven by winners")
    st.info("Research in progress: which valuation methods past winning teams used, and how the CFA curriculum teaches each step. Results land here, with links to the original reports.")
    st.subheader("How we assign work")
    c = st.columns(2)
    c[0].markdown("**A role is a first draft.** Each section has one person who writes the first draft. Everyone else reads, checks and can explain it.")
    c[1].markdown("**Join or leave a task.** Open a task and add or remove names. Two can share. If everyone leaves, it shows \"No owner yet\" and we pick someone on Monday.")
    c[0].markdown("**Four eyes on every number.** A task is Done only when a second person has checked it against the source.")
    c[1].markdown("**Two at a time.** Nobody holds more than two tasks in Doing. Finishing beats starting.")
    st.subheader("What lives where")
    c = st.columns(5)
    for col, (b_, s_) in zip(c, [("This app", "Plan, tasks, sources, notes, AI log, help hours, kickoff questions."),
                                 ("Excel", "The model and the assumption book: every input with its source."),
                                 ("Word or Google Docs", "The 10-page report and the appendix."),
                                 ("PowerPoint", "The presentation for the final."),
                                 ("Shared folder", "Linked in Team, so everyone finds the files.")]):
        col.markdown(f"**{b_}**  \n{s_}")


def page_trash():
    data = D()
    st.title("Trash")
    st.caption("Deleted tasks and notes wait here. Bring them back with one tap.")
    gone = [("tasks", t) for t in tasks(data, True) if t.get("deleted")] + [("notes", n) for n in notes(data, True) if n.get("deleted")]
    if not gone:
        st.caption("Trash is empty.")
    for col, x in gone:
        with st.container(border=True):
            c1, c2, c3 = st.columns([6, 1, 1], vertical_alignment="center")
            c1.markdown(f"**{e(x.get('title'))}**  \n<span class='rc-sub'>{'Task' if col == 'tasks' else 'Note'}</span>", unsafe_allow_html=True)
            if c2.button("Restore", key=f"r_{x['id']}"):
                write(store().patch, col, x["id"], {"deleted": False}, ok="Restored")
                st.rerun()
            if c3.button("Delete forever", key=f"d_{x['id']}", type="tertiary"):
                st.session_state[f"confirm_{x['id']}"] = True
            if st.session_state.get(f"confirm_{x['id']}"):
                st.warning("This cannot be undone.")
                if st.button("Yes, delete forever", key=f"dd_{x['id']}"):
                    write(store().delete, col, x["id"], ok="Deleted")
                    st.session_state.pop(f"confirm_{x['id']}", None)
                    st.rerun()


pages = [st.Page(page_board, title="Board", url_path="board", default=True),
         st.Page(page_team, title="Team", url_path="team"),
         st.Page(page_learn, title="Learn", url_path="learn"),
         st.Page(page_docs, title="Docs", url_path="docs"),
         st.Page(page_rules, title="Rules", url_path="rules"),
         st.Page(page_notes, title="Notes", url_path="notes"),
         st.Page(page_map, title="Map", url_path="map"),
         st.Page(page_trash, title="Trash", url_path="trash")]
if store().name == "local SQLite" and os.path.exists("/mount/src"):
    st.warning("Demo mode: the shared database is not connected yet, so changes made here can be lost when the app restarts. "
               "Keep using the claude.ai hub for real work until Supabase is connected (see DEPLOY.md).")
nav = st.navigation(pages, position="top")
nav.run()
st.caption(f"Data: {store().name}")
