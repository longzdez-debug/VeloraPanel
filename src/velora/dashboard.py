from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
HTML="""<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>VELORA</title><style>body{font:14px system-ui;margin:0;padding:24px;background:#0d0f12;color:#f4f4f5}h1{margin:0 0 18px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px}.card{background:#171a20;border:1px solid #2a2f38;border-radius:14px;padding:18px}.name{font-weight:700}.state{font-size:24px;margin:10px 0}.muted{color:#9299a5}</style></head><body><h1>VELORA PANEL</h1><div id=a class=grid></div><script>async function load(){const d=await (await fetch('/api/status')).json();a.innerHTML=d.accounts.map(x=>'<div class=card><div class=name>'+x.name+'</div><div class=state>'+x.state+'</div><div class=muted>WalkBot: '+x.walkbot+'</div></div>').join('')};load();setInterval(load,1000)</script></body></html>"""
class Dashboard:
 def __init__(self,supervisor,host="127.0.0.1",port=8765):self.s=supervisor;self.host=host;self.port=port;self.server=None
 def start(self):
  outer=self
  class H(BaseHTTPRequestHandler):
   def do_GET(self):
    if self.path=="/api/status":
     b=json.dumps({"running":outer.s.running,"accounts":[{"id":a.id,"name":a.name,"state":a.fsm.state.value,"walkbot":a.walkbot.fsm.state.value} for a in outer.s.accounts]}).encode()
     self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(b)
    else:
     b=HTML.encode();self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(b)
   def log_message(self,*args):pass
  self.server=ThreadingHTTPServer((self.host,self.port),H);Thread(target=self.server.serve_forever,daemon=True).start()
 def stop(self):
  if self.server:self.server.shutdown();self.server.server_close()
