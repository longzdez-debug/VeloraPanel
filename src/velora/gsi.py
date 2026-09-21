from __future__ import annotations
import hashlib,hmac,json,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from .model import GsiSnapshot
class GsiServer:
 def __init__(self,host="127.0.0.1",port=27100,token=""):
  self.host,self.port,self.token=host,port,token;self._last_digest=None;self._server=None;self._on_snapshot=None
 def on_snapshot(self,callback):self._on_snapshot=callback
 def start(self):
  outer=self
  class Handler(BaseHTTPRequestHandler):
   def do_POST(self):
    n=int(self.headers.get("Content-Length","0"));body=self.rfile.read(n)
    supplied=self.headers.get("X-Velora-Token","")
    if outer.token and not hmac.compare_digest(supplied,outer.token):self.send_response(401);self.end_headers();return
    digest=hashlib.sha256(body).hexdigest()
    if digest==outer._last_digest:self.send_response(204);self.end_headers();return
    outer._last_digest=digest
    try:data=json.loads(body)
    except json.JSONDecodeError:self.send_response(400);self.end_headers();return
    p=data.get("player") or {};st=p.get("state") or {};m=data.get("map") or {};r=data.get("round") or {}
    ps=st.get("position") or p.get("position") or ""
    pos=None
    if isinstance(ps,str):
     try: pos=tuple(float(x) for x in ps.split())[:3]
     except ValueError: pos=None
    snap=GsiSnapshot(time.monotonic(),(data.get("provider") or {}).get("timestamp"),m.get("name"),m.get("phase"),r.get("phase"),p.get("activity"),st.get("health"),p.get("steamid"),data)
    if pos is not None: snap.raw["_velora_position"]=pos
    if outer._on_snapshot:outer._on_snapshot(snap)
    self.send_response(204);self.end_headers()
   def log_message(self,*args):pass
  self._server=ThreadingHTTPServer((self.host,self.port),Handler);Thread(target=self._server.serve_forever,daemon=True).start()
 def stop(self):
  if self._server:self._server.shutdown();self._server.server_close();self._server=None
