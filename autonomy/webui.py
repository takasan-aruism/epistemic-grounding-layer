"""SLICE-7: thin Web UI (2DER autonomous loop v0). Browser correction surface for Taka —
NO git CLI required. stdlib http.server only (no external deps).

Reuses: autonomy.current_state.build_current_state (+ Taka overlay), autonomy.amend
(append-only events). Writes ONLY AUTONOMY_LEDGER.jsonl; NEVER the DE ledger or knowledge SoR.
Binds 0.0.0.0 so an iPhone on the same LAN / Tailscale can open it. v0: no auth, no deploy.

Run:  python3 autonomy/webui.py [--port 8787]
Open: http://<this-host-ip>:8787  (Mac browser / iPhone Safari)
"""
import sys, os, json, argparse, socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import autonomy.current_state as cs
import autonomy.amend as amend

# honest capability mapping for the Home free-text input (NO fake classifier: user picks type)
INPUT_TYPES = ["CORRECTION", "NOTE", "CONTEXT", "INCIDENT", "RESULT", "LOG", "QUESTION", "UNKNOWN"]
CAPABILITY = {
    "CORRECTION": "CAN_PROCESS_NOW",   # -> Taka correction event; HOLD/REJECT/PRIORITY have real overlay effect
    "NOTE": "CAN_RECORD_ONLY", "CONTEXT": "CAN_RECORD_ONLY",
    "INCIDENT": "CAN_RECORD_ONLY", "RESULT": "CAN_RECORD_ONLY", "LOG": "CAN_RECORD_ONLY",
    "QUESTION": "CAN_RECORD_ONLY",     # honest: no live autonomous answerer wired to the loop UI in v0
    "UNKNOWN": "CAN_RECORD_ONLY",
}
CAP_NOTE = ("autonomous processing of questions/incidents = NOT YET SUPPORTED "
            "(router/investigator SLICE-3/4 未実装). 今できるのは: 訂正の即時反映 と 入力の記録。")

HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>2DER</title><style>
:root{--bg:#0f1115;--fg:#e8e8ea;--mut:#8b93a0;--card:#191c22;--line:#2a2f38;--accent:#6ea3e0;
--good:#5fbf8f;--warn:#e0b25a;--bad:#e07a7a;--taka:#c88ce0}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.wrap{max-width:560px;margin:0 auto;padding:14px 14px 60px}
h1{font-size:19px;margin:6px 0 2px}.sub{color:var(--mut);font-size:12.5px;margin-bottom:12px}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}
.chip{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:4px 10px;font-size:12px;color:var(--mut)}
.chip b{color:var(--fg);font-variant-numeric:tabular-nums}
h2{font-size:12px;text-transform:uppercase;letter-spacing:.07em;color:var(--mut);margin:22px 0 8px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 13px;margin:9px 0}
.card.hold{border-left:3px solid var(--warn)}.card.pend{border-left:3px solid var(--taka)}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:20px;border:1px solid var(--line);color:var(--mut);margin:0 5px 5px 0}
.mono{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--mut);word-break:break-all}
textarea{width:100%;min-height:92px;background:#0b0d11;color:var(--fg);border:1px solid var(--line);
border-radius:10px;padding:11px;font:15px/1.45 inherit;resize:vertical}
.types{display:flex;gap:6px;flex-wrap:wrap;margin:9px 0}
.types button{background:#0b0d11;color:var(--mut);border:1px solid var(--line);border-radius:18px;padding:6px 11px;font-size:13px}
.types button.on{background:var(--accent);color:#06101c;border-color:var(--accent);font-weight:600}
.cap{font-size:12.5px;margin:6px 0 0;padding:8px 10px;border-radius:9px;background:#0b0d11;border:1px solid var(--line)}
.cap.now{color:var(--good)}.cap.rec{color:var(--warn)}.cap.no{color:var(--bad)}
.btns{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}
button.act{background:#0b0d11;color:var(--fg);border:1px solid var(--line);border-radius:9px;padding:9px 12px;font-size:13.5px;min-height:40px}
button.act:active{background:var(--line)}
button.pri{background:var(--accent);color:#06101c;border-color:var(--accent);font-weight:600}
button.send{width:100%;background:var(--accent);color:#06101c;border:none;border-radius:10px;padding:13px;font-size:16px;font-weight:600;margin-top:10px}
.eff{color:var(--good);font-size:12.5px;margin:3px 0}
details{margin-top:6px}summary{color:var(--mut);font-size:12.5px;cursor:pointer}
pre{background:#0b0d11;border:1px solid var(--line);border-radius:9px;padding:10px;overflow:auto;font-size:11px}
#toast{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);background:var(--accent);color:#06101c;
padding:9px 16px;border-radius:20px;font-size:13px;font-weight:600;opacity:0;transition:.2s;pointer-events:none}
#toast.show{opacity:1}.muted{color:var(--mut);font-size:13px}
</style></head><body><div class="wrap">
<h1>2DER capability surface</h1>
<div class="sub" id="asof">…</div>
<div class="chips" id="chips"></div>

<h2>2DER に渡す</h2>
<div class="card">
<textarea id="inp" placeholder="2DERに渡す"></textarea>
<div class="types" id="types"></div>
<div class="cap" id="cap">type を選ぶと、今のcapabilityで何ができるか表示します。</div>
<button class="send" onclick="send()">送信</button>
</div>

<h2>Taka decision queue</h2><div id="queue"></div>
<h2>Candidate work — ここで訂正</h2><div id="work"></div>
<h2>Applied corrections</h2><div id="eff"></div>
<details><summary>raw state (expand)</summary><pre id="raw"></pre></details>
</div><div id="toast"></div>
<script>
var TYPES=%TYPES%, CAP=%CAP%, CAPNOTE=%CAPNOTE%, curType=null, S=null;
function esc(s){return (s==null?'':''+s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function toast(t){var e=document.getElementById('toast');e.textContent=t;e.className='show';setTimeout(()=>e.className='',1400)}
function api(path,body){return fetch(path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},
  body:body?JSON.stringify(body):undefined}).then(r=>r.json())}
function amend(action,target,content,reason){return api('/api/amend',{action,target,content,reason}).then(st=>{render(st);toast(action)})}
function ask(action,target,label){var v=prompt(label);if(v!=null&&v!=='')amend(action,target,v)}
function renderTypes(){var h=document.getElementById('types');h.innerHTML='';TYPES.forEach(t=>{
  var b=document.createElement('button');b.textContent=t;b.className=(t===curType?'on':'');
  b.onclick=()=>{curType=t;renderTypes();var c=CAP[t],e=document.getElementById('cap');
    e.className='cap '+(c==='CAN_PROCESS_NOW'?'now':c==='CAN_RECORD_ONLY'?'rec':'no');
    e.textContent=t+' → '+c.replace(/_/g,' ')+'  ·  '+CAPNOTE};h.appendChild(b)})}
function send(){var txt=document.getElementById('inp').value.trim();if(!txt)return toast('空です');
  if(!curType)return toast('type を選んで');
  api('/api/inbox',{type:curType,text:txt}).then(r=>{render(r.state);document.getElementById('inp').value='';
    toast(curType+': '+r.capability.replace(/_/g,' '))})}
function workCard(w){var t=esc(w.kind),held=w.held_by?'<span class="tag" style="color:var(--taka)">HELD '+esc(w.held_by)+'</span>':'';
  return '<div class="card '+(w.held_by?'hold':'')+'"><span class="tag">P'+esc(w.priority)+'</span><span class="tag">'+t+'</span>'+held+
  '<div class="mono">ref: '+esc(JSON.stringify(w.ref))+'</div><div class="btns">'+
  '<button class="act" onclick="amend(\\'TAKA_HOLD\\',\\''+t+'\\',\\'hold\\')">HOLD</button>'+
  '<button class="act" onclick="amend(\\'TAKA_REJECT\\',\\''+t+'\\',\\'reject\\')">REJECT</button>'+
  '<button class="act" onclick="ask(\\'TAKA_PRIORITY_OVERRIDE\\',\\''+t+'\\',\\'新しい priority 数値\\')">PRIORITY</button>'+
  '<button class="act" onclick="ask(\\'TAKA_REDIRECT\\',\\''+t+'\\',\\'代わりに何をするか\\')">REDIRECT</button>'+
  '<button class="act" onclick="ask(\\'TAKA_CORRECTION\\',\\''+t+'\\',\\'訂正内容\\')">CORRECT</button>'+
  '<button class="act" onclick="amend(\\'TAKA_AUTHORITY_RECLASSIFICATION\\',\\''+t+'\\',\\'REQUIRES_TAKA\\')">THIS REQUIRES TAKA</button>'+
  '<button class="act" onclick="amend(\\'TAKA_AUTHORITY_RECLASSIFICATION\\',\\''+t+'\\',\\'DO_NOT_ASK\\')">DO NOT ASK ME THIS</button>'+
  '</div></div>'}
function render(st){S=st;
  document.getElementById('asof').textContent='as_of '+esc(st.as_of)+' · owner=Taka · v0 correction surface';
  var seals=st.seals||[],ok=seals.filter(s=>s.status==='OK').length;
  document.getElementById('chips').innerHTML=
    '<span class="chip">latest <b>'+esc(st.latest_de)+'</b></span>'+
    '<span class="chip">work <b>'+(st.candidate_executable_work||[]).length+'</b></span>'+
    '<span class="chip">pending <b>'+(st.authority_pending||[]).length+'</b></span>'+
    '<span class="chip">seals <b>'+ok+'/'+seals.length+'</b></span>'+
    '<span class="chip">val-fail <b>'+(st.validation_failures||[]).length+'</b></span>';
  var q=st.authority_pending||[];document.getElementById('queue').innerHTML=q.length?q.map(a=>
    '<div class="card pend"><span class="tag" style="color:var(--taka)">'+esc(a.action)+'</span><b>'+esc(a.target_object)+'</b>'+
    '<div class="muted">'+esc(a.content)+(a.reason?' · '+esc(a.reason):'')+' · '+esc(a.event_id)+'</div></div>').join(''):
    '<div class="muted">no active holds/redirects.</div>';
  var w=st.candidate_executable_work||[];document.getElementById('work').innerHTML=w.length?w.map(workCard).join(''):
    '<div class="muted">none pending.</div>';
  var e=st.taka_overlay_effects||[];document.getElementById('eff').innerHTML=e.length?e.map(x=>'<div class="eff">✓ '+esc(x)+'</div>').join(''):
    '<div class="muted">no corrections applied yet.</div>';
  document.getElementById('raw').textContent=JSON.stringify(st,null,2);}
renderTypes();api('/api/state').then(render);
</script></body></html>"""


def html_page():
    return (HTML.replace("%TYPES%", json.dumps(INPUT_TYPES))
                .replace("%CAP%", json.dumps(CAPABILITY))
                .replace("%CAPNOTE%", json.dumps(CAP_NOTE)))


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _json_body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    def log_message(self, *a):
        pass  # quiet

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            return self._send(200, html_page(), "text/html; charset=utf-8")
        if self.path == "/api/state":
            return self._send(200, json.dumps(cs.build_current_state(), ensure_ascii=False))
        self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        try:
            body = self._json_body()
            if self.path == "/api/amend":
                action = body.get("action")
                if action not in amend.ACTIONS:
                    return self._send(400, json.dumps({"error": f"bad action {action}"}))
                amend.append_taka_event(action, str(body.get("target", "")),
                                        str(body.get("content", "")), body.get("reason"))
                return self._send(200, json.dumps(cs.build_current_state(), ensure_ascii=False))
            if self.path == "/api/inbox":
                typ = str(body.get("type", "UNKNOWN"))
                cap = CAPABILITY.get(typ, "CAN_RECORD_ONLY")
                # recorded as an append-only context event (reuse existing action); NOT auto-processed in v0
                amend.append_taka_event("TAKA_CONTEXT_ADDITION", f"INBOX:{typ}",
                                        str(body.get("text", "")), reason=cap)
                return self._send(200, json.dumps({"state": cs.build_current_state(), "capability": cap},
                                                  ensure_ascii=False))
            self._send(404, json.dumps({"error": "not found"}))
        except Exception as e:
            self._send(500, json.dumps({"error": f"{type(e).__name__}: {e}"}))


def _lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def make_server(port, ledger=None):
    if ledger:
        amend.AUTONOMY_LEDGER = cs.AUTONOMY_LEDGER = ledger
    return ThreadingHTTPServer(("0.0.0.0", port), Handler)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    a = ap.parse_args()
    srv = make_server(a.port)
    ip = _lan_ip()
    print(f"2DER web UI on http://0.0.0.0:{a.port}")
    print(f"  Mac browser / iPhone Safari:  http://{ip}:{a.port}   (same LAN / Tailscale)")
    print(f"  writes ONLY {amend.AUTONOMY_LEDGER} (append-only); DE ledger / SoR untouched.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
