"""Shared helpers: styling, people, dates and task logic."""
import datetime as dt
import html

import streamlit as st

from .content import COLORS, ROLES

MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

CSS = """
<style>
.block-container { padding-top: 4.2rem; max-width: 1100px; }
h1, h2, h3 { letter-spacing: -.01em; }
.rc-sub { color:#676b74; font-size:13px; }
.rc-count { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }
@media (max-width:640px){ .rc-count { grid-template-columns:repeat(2,1fr); } }
.rc-tile { background:#fff; border:1px solid #e6e6e9; box-shadow:0 1px 2px rgba(0,0,0,.04),0 4px 14px rgba(0,0,0,.04); border-radius:16px; padding:14px 16px; }
.rc-tile.next { background:linear-gradient(135deg,#8f1225,#b0182d); border-color:transparent; color:#fff; }
.rc-tile .n { font-size:34px; font-weight:800; line-height:1; letter-spacing:-.03em; }
.rc-tile .u { font-size:13px; font-weight:700; opacity:.75; margin-left:3px; }
.rc-tile .w { font-weight:700; margin-top:8px; }
.rc-tile .d { font-size:12px; opacity:.7; }
.rc-av { width:26px; height:26px; border-radius:50%; display:inline-grid; place-items:center; color:#fff; font-weight:800; font-size:12px; border:2px solid #fff; text-shadow:0 1px 2px rgba(0,0,0,.45); vertical-align:middle; }
.rc-stack .rc-av { width:20px; height:20px; font-size:9px; margin-left:-5px; }
.rc-stack .rc-av:first-child { margin-left:0; }
.rc-colh { display:flex; align-items:center; gap:8px; font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:.08em; color:#676b74; margin:0 0 6px; }
.rc-colh .dot { width:8px; height:8px; border-radius:50%; }
.rc-colh .c { margin-left:auto; background:#f1f1f3; border-radius:999px; padding:0 8px; color:#18191d; }
.rc-ph { display:inline-block; font-size:9px; font-weight:800; letter-spacing:.04em; text-transform:uppercase; color:#b0182d; background:#f7e1e4; border-radius:999px; padding:1px 7px; max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.rc-ph.role { color:#676b74; background:#eeeae5; }
.rc-t { font-weight:700; font-size:13px; line-height:1.25; margin:4px 0; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
.rc-t.done { color:#676b74; text-decoration:line-through; }
.rc-m { font-size:11px; color:#676b74; }
.rc-ck { font-weight:800; color:#2b7655; } .rc-ck.half { color:#a2660b; }
.rc-late { color:#b0182d; font-weight:800; }
.rc-bar { height:4px; border-radius:3px; background:#eeeae5; overflow:hidden; margin:5px 0 4px; }
.rc-bar i { display:block; height:100%; background:#2b7655; }
[class*="st-key-card_"] { background:#fff; border-radius:10px !important; min-height:150px; box-shadow:0 1px 2px rgba(0,0,0,.04),0 4px 12px rgba(0,0,0,.05); }
[class*="st-key-card_"] button { min-height:26px; padding:0 9px; font-size:12px; }
[class*="st-key-card_"] [class*="st-key-row_"] { flex-wrap:nowrap; }
.rc-box { background:#fff; border:1px solid #e2dcd5; border-radius:16px; padding:14px 16px; margin-bottom:10px; }
.rc-k { font-size:11px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; color:#b0182d; }
.rc-muted { color:#676b74; font-size:14px; }
.rc-score { display:flex; height:54px; border-radius:12px; overflow:hidden; margin:8px 0; }
.rc-score div { display:flex; flex-direction:column; justify-content:center; align-items:center; color:#fff; font-weight:800; border-right:2px solid #ffffff; min-width:0; line-height:1.1; text-align:center; }
.rc-score span { font-size:10px; font-weight:700; opacity:.85; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:100%; }
.rc-mstep { border:1px solid #e2dcd5; border-radius:16px; overflow:hidden; background:#fff; margin-bottom:12px; }
.rc-mstep .h { background:#18191d; color:#f4f2ef; padding:12px 16px; display:flex; gap:14px; align-items:baseline; flex-wrap:wrap; }
.rc-mstep .h .n { font-size:26px; font-weight:800; color:#ff8c9c; }
.rc-mstep .h b { font-size:17px; } .rc-mstep .h .w { font-size:12px; opacity:.7; }
.rc-mstep .c { display:grid; grid-template-columns:1fr 1fr; }
.rc-mstep .c > div { padding:12px 16px; font-size:14px; }
.rc-mstep .c > div + div { border-left:1px solid #e2dcd5; }
@media (max-width:700px){ .rc-mstep .c { grid-template-columns:1fr; } .rc-mstep .c > div + div { border-left:0; border-top:1px solid #e2dcd5; } }
.rc-parts { display:grid; grid-template-columns:repeat(4,1fr); border-top:1px solid #e2dcd5; }
@media (max-width:900px){ .rc-parts { grid-template-columns:1fr 1fr; } }
@media (max-width:520px){ .rc-parts { grid-template-columns:1fr; } }
.rc-part { padding:10px 14px; font-size:13px; border-right:1px solid #e2dcd5; }
.rc-part:last-child { border-right:0; }
.rc-part.now { background:#f7e1e4; }
.rc-part .pn { font-weight:800; font-size:14px; }
.rc-part .badge { font-size:10px; font-weight:800; text-transform:uppercase; background:#b0182d; color:#fff; border-radius:999px; padding:1px 7px; margin-left:4px; }
.rc-part .badge.done { background:#2b7655; }
.rc-part ul { list-style:none; padding:0; margin:6px 0 0; font-size:12px; }
.rc-lane { display:grid; grid-template-columns:90px 1fr 42px; gap:10px; align-items:center; margin:6px 0; }
.rc-rail { position:relative; height:28px; border-radius:14px; background:#eeeae5; margin:0 14px; }
.rc-rail .rc-av { position:absolute; top:1px; transform:translateX(-50%); }
.rc-rail .tl { position:absolute; top:-3px; bottom:-3px; width:2px; background:#b0182d; opacity:.6; }
.rc-track { position:relative; height:60px; margin:18px 14px 0; }
.rc-zone { position:absolute; top:24px; height:10px; border-radius:5px; }
.rc-zone span { position:absolute; top:12px; left:0; font-size:10px; font-weight:800; color:#676b74; white-space:nowrap; }
.rc-station { position:absolute; top:0; transform:translateX(-50%); font-size:11px; font-weight:800; white-space:nowrap; }
.rc-station.low { top:40px; }
.rc-today { position:absolute; top:-14px; bottom:-4px; width:2px; background:#b0182d; }
.rc-today b { position:absolute; top:-16px; left:50%; transform:translateX(-50%); font-size:10px; color:#b0182d; }
</style>
"""


def inject_css():
    st.html(CSS)


def e(x):
    return html.escape(str(x if x is not None else ""))


def today():
    return dt.date.today().isoformat()


def days(iso):
    return (dt.date.fromisoformat(iso) - dt.date.today()).days


def fd(iso):
    if not iso:
        return ""
    d = dt.date.fromisoformat(iso)
    return f"{MON[d.month - 1]} {d.day}"


# ---- people -------------------------------------------------------------
def members(D):
    return list((D.get("meta", {}).get("team", {}) or {}).get("members", []))


def member(D, mid):
    return next((m for m in members(D) if m.get("id") == mid), None)


def label(D, mid):
    if mid == "all":
        return "Everyone"
    if not mid:
        return "No owner yet"
    m = member(D, mid)
    return (m.get("name") or "?") if m else "Former member"


def color(D, mid):
    if mid == "all":
        return "#4a5568"
    ms = members(D)
    for i, m in enumerate(ms):
        if m.get("id") == mid:
            c = m.get("color") or ""
            return c if len(c) == 7 and c.startswith("#") else COLORS[i % len(COLORS)]
    return "#9aa0aa"


def av(D, mid, size=None):
    ch = "★" if mid == "all" else ("?" if not mid else (label(D, mid)[:1].upper() or "?"))
    style = ("background:#18191d;color:#FFE600" if mid == "all" else f"background:{color(D, mid)}") + (f";width:{size}px;height:{size}px;font-size:{int(size*0.4)}px" if size else "")
    return f'<span class="rc-av" style="{style}" title="{e(label(D, mid))}">{e(ch)}</span>'


# ---- tasks ----------------------------------------------------------------
def owners(D, t):
    a = [x for x in (t.get("assignees") or []) if x]
    if not a and t.get("owner"):
        a = [t["owner"]]
    if a:
        return a
    if t.get("role"):
        m = next((x for x in members(D) if x.get("role") == t["role"]), None)
        if m:
            return [m["id"]]
    return []


def has(D, t, mid):
    o = owners(D, t)
    return (not o) if mid == "" else (mid in o)


def is_mine(D, t, mid):
    o = owners(D, t)
    return mid in o or "all" in o


def steps_info(t):
    st_ = t.get("steps") or []
    if not st_:
        return ""
    d = sum(1 for x in st_ if x.get("d"))
    return f'<span class="rc-ck{" half" if d < len(st_) else ""}">☑ {d}/{len(st_)}</span>'


def steps_bar(t):
    st_ = t.get("steps") or []
    if not st_ or t.get("status") == "done":
        return ""
    d = sum(1 for x in st_ if x.get("d"))
    return f'<div class="rc-bar"><i style="width:{d / len(st_) * 100:.0f}%"></i></div>'


def by_due(t):
    return (t.get("due") or "9999", t.get("created") or 0)


def sprints_sorted(D):
    return sorted((D.get("sprints") or {}).values(), key=lambda s: s.get("start") or "")


def current_sprint_id(D):
    lst, t = sprints_sorted(D), today()
    for s in lst:
        if s["start"] <= t <= s["end"]:
            return s["id"]
    for s in lst:
        if s["start"] > t:
            return s["id"]
    return lst[-1]["id"] if lst else "backlog"


def in_sprint(D, t, sid):
    ids = {s["id"] for s in sprints_sorted(D)}
    return (t.get("sprint") not in ids) if sid == "backlog" else t.get("sprint") == sid


def role_name(key):
    return ROLES[key][0] if key in ROLES else ""
