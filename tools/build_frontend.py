"""Build the Streamlit frontend from the claude.ai hub page, so both look identical.

Usage:
    python -I tools/build_frontend.py <path to team_hub.html> <app_dir>

Wraps team_hub.html in a full HTML document and injects a small bridge that
replaces the claude.ai `db` with Streamlit's custom-component messages:
the page receives all data from Python, and every write (set, update, delete)
is queued and sent back to Python, which saves it and acknowledges it.
Writes stay in the queue until Python confirms them, so fast clicks are never lost.
"""
import io
import os
import sys

BRIDGE = r"""<script>
(function(){
  var STORE = {}, colSubs = {}, docSubs = {}, queue = [], ready, readyP = new Promise(function(r){ ready = r; });
  function post(m){ m.isStreamlitMessage = true; window.parent.postMessage(m, "*"); }
  function clone(x){ return JSON.parse(JSON.stringify(x)); }
  function snap(col){ var m = STORE[col] || {}; return {docs: Object.keys(m).map(function(k){ var d = m[k]; return {id:k, exists:true, data:function(){ return d; }}; })}; }
  function emit(col){
    (colSubs[col] || []).forEach(function(cb){ try { cb(snap(col)); } catch(e){ console.error(e); } });
    Object.keys(docSubs).forEach(function(p){ var a = p.split("/"); if (a[0] !== col) return; var d = (STORE[col] || {})[a[1]];
      docSubs[p].forEach(function(cb){ try { cb({id:a[1], exists:!!d, data:function(){ return d; }}); } catch(e){ console.error(e); } }); });
  }
  function apply(o){
    var m = STORE[o.col] = STORE[o.col] || {};
    if (o.kind === "set") m[o.id] = clone(o.data);
    else if (o.kind === "update") { if (!m[o.id]) return false; m[o.id] = Object.assign({}, m[o.id], clone(o.data)); }
    else if (o.kind === "delete") delete m[o.id];
    return true;
  }
  function send(){ post({type:"streamlit:setComponentValue", value:{ops:queue.slice(), t:Date.now()}, dataType:"json"}); }
  function write(o){
    if (!apply(o)) return Promise.reject({code:"invalid_argument", message:"Not found"});
    o.opid = "o" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
    queue.push(o); send(); emit(o.col); return Promise.resolve();
  }
  function ref(col, id){
    return {id:id, path:col + "/" + id,
      set:function(d){ return write({kind:"set", col:col, id:id, data:d}); },
      update:function(d){ return write({kind:"update", col:col, id:id, data:d}); },
      delete:function(){ return write({kind:"delete", col:col, id:id}); },
      onSnapshot:function(cb){ var p = col + "/" + id; (docSubs[p] = docSubs[p] || []).push(cb);
        readyP.then(function(){ var d = (STORE[col] || {})[id]; cb({id:id, exists:!!d, data:function(){ return d; }}); }); return function(){}; }};
  }
  function newId(){ return "x" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8); }
  var db = {
    collection:function(col){ return {path:col, doc:function(id){ return ref(col, id || newId()); },
      onSnapshot:function(cb){ (colSubs[col] = colSubs[col] || []).push(cb); readyP.then(function(){ cb(snap(col)); }); return function(){}; }}; },
    doc:function(p){ var a = p.split("/"); return ref(a[0], a[1]); }
  };
  var yes = function(){ return Promise.resolve(true); };
  window.claude = {use:function(name){
    if (name === "db") return readyP.then(function(){ return db; });
    if (name === "user") return Promise.resolve({can:yes, isOwner:yes, canEdit:yes});
    return Promise.resolve(null);
  }};
  function fit(){
    var h = 900;
    try { h = window.parent.innerHeight || h; } catch(e) {}
    post({type:"streamlit:setFrameHeight", height:h});
  }
  window.addEventListener("resize", fit);
  window.addEventListener("message", function(ev){
    var m = ev.data; if (!m || m.type !== "streamlit:render") return;
    var args = m.args || {}, acked = args.acked || [];
    queue = queue.filter(function(o){ return acked.indexOf(o.opid) < 0; });
    STORE = clone(args.data || {});
    queue.forEach(apply);
    if (ready) { ready(); ready = null; }
    var cols = {}; Object.keys(STORE).concat(Object.keys(colSubs)).forEach(function(c){ cols[c] = 1; });
    Object.keys(cols).forEach(emit);
    var b = document.getElementById("banner");
    if (b && args.demo && !b.classList.contains("on")) { b.textContent = args.demo; b.classList.add("on"); }
    fit();
  });
  post({type:"streamlit:componentReady", apiVersion:1});
})();
</script>"""


def main(src, app):
    page = io.open(src, encoding="utf-8").read()
    doc = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width,initial-scale=1">' + BRIDGE + "</head><body>\n" + page + "\n</body></html>\n")
    out = os.path.join(app, "frontend")
    os.makedirs(out, exist_ok=True)
    io.open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(doc)
    print("frontend/index.html written,", len(doc), "chars")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
