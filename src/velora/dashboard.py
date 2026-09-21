from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
HTML="""<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>VELORA PANEL</title><style>*{box-sizing:border-box}body{font:14px system-ui;margin:0;padding:28px;background:#090b0f;color:#eef0f3}header{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}.card{background:#141820;border:1px solid #282f3a;border-radius:16px;padding:20px}.pill{display:inline-block;padding:5px 9px;border-radius:99px;background:#202733}.big{font-size:25px;font-weight:750;margin:14px 0}.muted{color:#8d97a6}button{background:#eef0f3;color:#111;border:0;border-radius:9px;padding:8px 12px;cursor:pointer}</style></head><body><header><div><h1>VELORA PANEL</h1><div class=muted>Supervisor / FSM / GSI / WalkBot</div></div><div id=h class=pill>offline</div></header><div id=a class=grid></div><script>async function load(){let d=await(await fetch('/api/status')).json();h.textContent=d.running?'RUNNING':'STOPPED';a.innerHTML=d.accounts.map(x=>'<div class=card><strong>'+x.name+'</strong><div class=big>'+x.state+'</div><div class=muted>WalkBot: '+x.walkbot+'</div><div class=muted>GSI: '+(x.gsi_age==null?'—':x.gsi_age.toFixed(1)+'s')+'</div></div>').join('')}load();setInterval(load,500)</script></body></html>"""
class Dashboard:
 def __init__(self,supervisor,host="127.0.0.1",port=8765):self.s=supervisor;self.host=host;self.port=port;self.server=None
 def start(self):
  outer=self
  class H(BaseHTTPRequestHandler):
   def do_GET(self):
    if self.path=="/api/status":
     now=__import__("time").monotonic()
     b=json.dumps({"running":outer.s.running,"accounts":[{"id":a.id,"name":a.name,"state":a.fsm.state.value,"walkbot":a.walkbot.fsm.state.value,"gsi_age":None if a.walkbot.last_position is None else max(0,now-a.walkbot.last_progress)} for a in outer.s.accounts]}).encode()
     self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(b)
    else:
     b=HTML.encode();self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(b)
   def log_message(self,*args):pass
  self.server=ThreadingHTTPServer((self.host,self.port),H);Thread(target=self.server.serve_forever,daemon=True).start()
 def stop(self):
  if self.server:self.server.shutdown();self.server.server_close();self.server=None
