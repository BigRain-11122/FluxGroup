#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""web_ai.py - one page so friends and fleet machines can use this Mac's local model.

Safety: passcode, concurrency cap 2, ctx<=8192, output<=600, every call audited.
Run: WEB_PASSCODE=xxx python3 Tools/fleet/web_ai.py --port 8088
"""
import json, os, secrets, sys, threading, time, urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UP = "http://127.0.0.1:11434"
PORT = int(os.environ.get("WEB_PORT", "8088"))
MAX_CONC = int(os.environ.get("WEB_MAX_CONC", "2"))
PASSCODE = os.environ.get("WEB_PASSCODE") or secrets.token_urlsafe(6)
MODELS = ["qwen3.5:4b", "qwen3.5:35b-a3b"]
# Endpoint catalogue: each entry is "where the compute lives". bm-d (3xV100) joins by adding
# one row here once it reports; the page shows it as offline until then.
CATALOG = [
    {"id": "qwen3.5:4b", "label": "快速 · 4B", "machine": "bm-m 本机",
     "note": "判读/写作，约 40 tok/s，占 4.2GB"},
    {"id": "qwen3.5:35b-a3b", "label": "深度 · 35B-A3B", "machine": "bm-m 本机（按需）",
     "note": "重活，21GB，冷启动约 20 秒"},
    {"id": "bm-d/qwen3.5:35b-a3b", "label": "算力大脑 · V100×3", "machine": "bm-d",
     "note": "上线后自动出现；当前未入网"},
]
SEM = threading.Semaphore(MAX_CONC)
AUDIT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     "cph4", "fleet", "dispatcher", "events.jsonl")

PAGE = """<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>FLUX 本地模型</title><style>
*{box-sizing:border-box;margin:0;padding:0}body{background:#0a0e16;color:#e3eaf6;height:100vh;
font:15px/1.65 -apple-system,'PingFang SC',sans-serif;display:flex;flex-direction:column}
header{padding:14px 20px;border-bottom:1px solid #1f2b42;display:flex;gap:10px;align-items:center}
h1{font-size:15px;font-weight:600}select,input,button,textarea{background:#101826;color:#e3eaf6;
border:1px solid #1f2b42;border-radius:8px;padding:8px 10px;font:inherit}
button{cursor:pointer}button:hover{border-color:#2fd08a}#log{flex:1;overflow-y:auto;padding:20px;
display:flex;flex-direction:column;gap:12px}.m{max-width:760px;padding:12px 14px;border-radius:12px;
white-space:pre-wrap;word-break:break-word}.u{align-self:flex-end;background:#16233c}
.a{align-self:flex-start;background:#101826;border:1px solid #1f2b42}
.r{font-size:11px;color:#7a8aa5;margin-bottom:4px}footer{padding:14px 20px;border-top:1px solid #1f2b42;
display:flex;gap:10px}footer textarea{flex:1;resize:none;height:54px}
.hint{font-size:11px;color:#56647f;padding:6px 20px 0}</style></head><body>
<header><h1>⚡ FLUX 本地模型</h1><select id="m"></select>
<input id="pw" type="password" placeholder="访问口令" style="width:150px">
<button onclick="clr()">清空</button></header><div id="log"></div>
<div class="hint">由这台 Mac 本地推理，不走云端；重档模型需排队。</div>
<footer><textarea id="q" placeholder="问点什么…（Enter 发送）"></textarea>
<button id="s" onclick="send()">发送</button></footer><script>
const log=document.getElementById('log'),q=document.getElementById('q'),m=document.getElementById('m'),
pw=document.getElementById('pw'),hist=[];
fetch('/api/models').then(r=>r.json()).then(list=>{
 list.forEach(x=>{const o=document.createElement('option');o.value=x.id;
  o.textContent=x.label+' · '+x.machine+(x.loaded?' · 已加载':'');
  if(x.machine.indexOf('bm-d')>-1){o.disabled=true;o.textContent=x.label+' · 未上线'}
  else m.appendChild(o)})})
pw.value=localStorage.getItem('pw')||'';
function add(role,t){const d=document.createElement('div');d.className='m '+(role=='user'?'u':'a');
d.innerHTML='<div class="r">'+(role=='user'?'你':'本地模型')+'</div>';d.appendChild(document.createTextNode(t));
log.appendChild(d);log.scrollTop=log.scrollHeight;return d}
function clr(){log.innerHTML='';hist.length=0}
q.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
async function send(){const t=q.value.trim();if(!t)return;q.value='';localStorage.setItem('pw',pw.value);
add('user',t);hist.push({role:'user',content:t});const box=add('assistant','…');document.getElementById('s').disabled=true;
try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({passcode:pw.value,model:m.value,messages:hist.slice(-8)})});const d=await r.json();
box.lastChild.nodeValue=d.text||('⚠️ '+(d.error||'无响应'));if(d.text)hist.push({role:'assistant',content:d.text})}
catch(e){box.lastChild.nodeValue='⚠️ 连接失败'}document.getElementById('s').disabled=false;log.scrollTop=log.scrollHeight}
</script></body></html>"""


def audit(row):
    row["ts"] = datetime.now().isoformat(timespec="seconds")
    try:
        with open(AUDIT, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, body, ctype="application/json"):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._send(200, PAGE, "text/html; charset=utf-8")
        if self.path.startswith("/api/models"):
            live = []
            try:
                with urllib.request.urlopen(UP + "/api/ps", timeout=4) as r:
                    live = [m.get("name") or m.get("model") for m in json.load(r).get("models", [])]
            except Exception:
                pass
            out = [dict(c, loaded=(c["id"] in live), available=True) for c in CATALOG]
            return self._send(200, json.dumps(out, ensure_ascii=False))
        if self.path.startswith("/healthz"):
            return self._send(200, json.dumps({"ok": True, "max_conc": MAX_CONC}))
        self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._send(400, json.dumps({"error": "bad json"}))
        if body.get("passcode") != PASSCODE:
            return self._send(401, json.dumps({"error": "口令不正确"}))
        model = body.get("model") if body.get("model") in MODELS else MODELS[0]
        msgs = (body.get("messages") or [])[-8:]
        if not SEM.acquire(timeout=45):
            return self._send(429, json.dumps({"error": "排队已满，稍后再试"}))
        t0 = time.time()
        try:
            payload = {"model": model, "messages": msgs, "stream": False, "think": False,
                       "options": {"num_ctx": 8192, "num_predict": 600, "temperature": 0.7}}
            req = urllib.request.Request(UP + "/api/chat", data=json.dumps(payload).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=900) as r:
                d = json.load(r)
            text = ((d.get("message") or {}).get("content") or "").strip()
            audit({"kind": "web", "model": model, "sec": round(time.time() - t0, 1),
                   "chars": len(text)})
            self._send(200, json.dumps({"text": text}, ensure_ascii=False))
        except Exception as e:
            audit({"kind": "web", "model": model, "error": str(e)[:120]})
            self._send(502, json.dumps({"error": str(e)[:120]}))
        finally:
            SEM.release()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    if "--port" in sys.argv:
        PORT = int(sys.argv[sys.argv.index("--port") + 1])
    print("[web] http://0.0.0.0:%d passcode=%s max_conc=%d" % (PORT, PASSCODE, MAX_CONC))
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()