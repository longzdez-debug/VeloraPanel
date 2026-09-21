from __future__ import annotations
import hashlib,hmac,json,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from .model import GsiSnapshot
def _vec(value):
 if not isinstance(value,str): return None
 try:
  x=[float(v) for v in value.replace(","," ").split()]
  return tuple(x[:3]) if len(x)>=3 else None
 except ValueError:return None
class GsiServer:
 def __init__(self,host="127.0.0.1",port=27100,token=""):
  self.host,self.port,self.token=host,port,token;self._last_key=None;self.last_received=None;self._server=None;self._on_snapshot=None
 def on_snapshot(self,callback):self._on_snapshot=callback
 def start(self):
  outer=self
  class Handler(BaseHTTPRequestHandler):
   def do_POST(self):
    try:n=int(self.headers.get("Content-Length","0"));body=self.rfile.read(n)
    except ValueError:self.send_response(400);self.end_headers();return
    try:data=json.loads(body)
    except json.JSONDecodeError:self.send_response(400);self.end_headers();return
    auth=data.get("auth") or {}
    supplied=auth.get("token","") if isinstance(auth,dict) else ""
    if outer.token and not hmac.compare_digest(str(supplied),outer.token):
     self.send_response(401);self.end_headers();return
    provider=data.get("provider") or {};m=data.get("map") or {};r=data.get("round") or {};p=data.get("player") or {};st=p.get("state") or {}
    position=_vec(p.get("position") or st.get("position"))
    forward=_vec(p.get("forward") or p.get("forward_direction"))
    ts=provider.get("timestamp")
    key=(ts,hashlib.sha256(body).hexdigest())
    if key==outer._last_key:self.send_response(204);self.end_headers();return
    outer._last_key=key;outer.last_received=time.monotonic()
    rn=m.get("round")
    try:rn=int(rn) if rn is not None else None
    except (TypeError,ValueError):rn=None
    snap=GsiSnapshot(time.monotonic(),ts,m.get("name"),m.get("phase"),r.get("phase"),p.get("activity"),st.get("health"),p.get("steamid"),position,forward,rn,data)
    if outer._on_snapshot:outer._on_snapshot(snap)
    self.send_response(204);self.end_headers()
   def log_message(self,*args):pass
  self._server=ThreadingHTTPServer((self.host,self.port),Handler);Thread(target=self._server.serve_forever,daemon=True).start()
 def stop(self):
  if self._server:self._server.shutdown();self._server.server_close();self._server=None
