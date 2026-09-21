from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
class Dashboard:
 def __init__(self,supervisor,host="127.0.0.1",port=8765): self.supervisor=supervisor;self.host=host;self.port=port;self.server=None
 def start(self):
  outer=self
  class H(BaseHTTPRequestHandler):
   def do_GET(self):
    if self.path=="/api/status":
     body=json.dumps({"running":outer.supervisor.running,"accounts":[{"id":a.id,"name":a.name,"state":a.fsm.state.value,"walkbot":a.walkbot.fsm.state.value} for a in outer.supervisor.accounts]}).encode()
     self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(body);return
    body=HTML.encode();self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.end_headers();self.wfile.write(body)
   def log_message(self,*args):pass
  self.server=ThreadingHTTPServer((self.host,self.port),H);Thread(target=self.server.serve_forever,daemon=True).start()
 def stop(self):
  if self.server:self.server.shutdown();self.server.server_close()
HTML="""<!doctype html><html><head><meta charset=utf-8><title>VELORA PANEL</title><style>body{font:14px system-ui;background:#101216;color:#eee;margin:0;padding:24px}h1{margin-top:0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}.card{background:#191c22;border:1px solid #2b3039;border-radius:12px;padding:16px}.state{font-size:22px;margin:8px 0}</style></head><body><h1>VELORA PANEL</h1><div id="a" class="grid"></div><script>async function r(){let x=await fetch('/api/status');let d=await x.json();document.querySelector('#a').innerHTML=d.accounts.map(a=>'<div class="card"><b>'+a.name+'</b><div class="state">'+a.state+'</div><div>WalkBot: '+a.walkbot+'</div></div>').join('')}r();setInterval(r,1000)</script></body></html>"""
