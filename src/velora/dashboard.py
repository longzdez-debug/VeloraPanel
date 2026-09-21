from __future__ import annotations
import json,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlparse
HTML="""<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>VELORA PANEL</title><style>*{box-sizing:border-box}body{font:14px system-ui;margin:0;padding:24px;background:#090b0f;color:#eef0f3}header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}.card{background:#141820;border:1px solid #282f3a;border-radius:14px;padding:18px}.pill{padding:5px 9px;border-radius:99px;background:#202733}.big{font-size:24px;font-weight:750;margin:10px 0}.muted{color:#8d97a6}button{background:#eef0f3;color:#111;border:0;border-radius:8px;padding:7px 10px;margin:3px;cursor:pointer}.danger{background:#e9baba}input{background:#0d1117;color:#fff;border:1px solid #303744;border-radius:7px;padding:7px;width:90px}</style></head><body><header><div><h1>VELORA PANEL</h1><div class=muted>Control plane / FSM / GSI / WalkBot / Routes</div></div><div id=h class=pill>offline</div></header><div id=a class=grid></div><section class=card style="margin-top:16px"><h2>Route editor</h2><div class=muted>Создание waypoint требует координат из GSI.</div><input id=map placeholder="map"><input id=nid placeholder="id"><input id=x placeholder="x"><input id=y placeholder="y"><input id=z placeholder="z"><button onclick="node()">Add waypoint</button><br><input id=ra placeholder="from"><input id=rb placeholder="to"><button onclick="edge()">Connect</button><button onclick="save()">Save map</button><pre id=r></pre></section><script>
async function api(u,m='GET',body){let q={method:m,headers:{'Content-Type':'application/json'}};if(body)q.body=JSON.stringify(body);let z=await fetch(u,q);return z.json()}
async function act(id,op){await api('/api/accounts/'+id+'/'+op,'POST');load()}
async function kill(){await api('/api/emergency-stop','POST');load()}
async function node(){r.textContent=JSON.stringify(await api('/api/routes/'+map.value+'/nodes','POST',{id:nid.value,x:+x.value,y:+y.value,z:+z.value}),null,2)}
async function edge(){r.textContent=JSON.stringify(await api('/api/routes/'+map.value+'/edges','POST',{a:ra.value,b:rb.value}),null,2)}
async function save(){r.textContent=JSON.stringify(await api('/api/routes/'+map.value+'/save','POST'),null,2)}
async function load(){let d=await api('/api/status');h.textContent=(d.kill_switch?'KILL SWITCH':'')+(d.running?' RUNNING':' STOPPED');a.innerHTML=d.accounts.map(x=>'<div class=card><strong>'+x.name+'</strong><div class=big>'+x.state+'</div><div class=muted>WalkBot: '+x.walkbot+' | PID: '+(x.process_id||'—')+'</div><div class=muted>Route: '+(x.route_map||'—')+'</div><div class=muted>GSI: '+(x.gsi_age==null?'—':x.gsi_age.toFixed(1)+'s')+'</div><button onclick="act(\''+x.id+'\',\'start\')">Start</button><button onclick="act(\''+x.id+'\',\'stop\')">Stop</button><button class=danger onclick="act(\''+x.id+'\',\'kill\')">Kill WalkBot</button></div>').join('')}
load();setInterval(load,700)</script><button class=danger onclick="kill()">EMERGENCY STOP ALL</button></body></html>"""
class Dashboard:
 def __init__(self,supervisor,host="127.0.0.1",port=8765):self.s=supervisor;self.host=host;self.port=port;self.server=None
 def start(self):
  outer=self
  class H(BaseHTTPRequestHandler):
   def _json(self,obj,status=200):
    b=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header("Content-Type","application/json");self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(b)
   def do_GET(self):
    p=urlparse(self.path).path
    if p=="/api/status":
     now=time.monotonic();return self._json({"running":outer.s.running,"kill_switch":outer.s.kill_switch,"accounts":[{"id":a.id,"name":a.name,"state":a.fsm.state.value,"walkbot":a.walkbot.fsm.state.value,"process_id":a.process_id,"route_map":getattr(a,"route_map",None),"gsi_age":None if a.walkbot.last_gsi is None else max(0,now-a.walkbot.last_gsi)} for a in outer.s.accounts]})
    if p.startswith("/api/routes/"):
     map_name=p.split("/")[3];return self._json(outer.s.route_store.get(map_name).to_dict())
    b=HTML.encode();self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(b)
   def do_POST(self):
    p=urlparse(self.path).path;parts=[x for x in p.split("/") if x]
    try:
     if parts==["api","emergency-stop"]:outer.s.emergency_stop();return self._json({"ok":True})
     if len(parts)==4 and parts[:2]==["api","accounts"]:
      a=outer.s.get_account(parts[2])
      if not a:return self._json({"error":"account not found"},404)
      if parts[3]=="start":outer.s.start_account(a.id)
      elif parts[3]=="stop":outer.s.stop_account(a.id)
      elif parts[3]=="kill":a.walkbot.emergency_stop()
      else:return self._json({"error":"unknown action"},404)
      return self._json({"ok":True})
     if len(parts)==4 and parts[:2]==["api","routes"]:
      map_name=parts[2];g=outer.s.route_store.get(map_name);data=json.loads(self.rfile.read(int(self.headers.get("Content-Length","0")) or 0) or b"{}")
      if parts[3]=="nodes":from .routes import Node;g.add(Node(str(data["id"]),float(data["x"]),float(data["y"]),float(data.get("z",0))))
      elif parts[3]=="edges":g.connect(str(data["a"]),str(data["b"]))
      elif parts[3]=="save":outer.s.route_store.save(map_name,g);return self._json({"ok":True,"validation":g.validate()})
      else:return self._json({"error":"unknown route action"},404)
      return self._json(g.to_dict())
    return self._json({"error":"not found"},404)
    except Exception as e:return self._json({"error":str(e)},400)
   def log_message(self,*args):pass
  self.server=ThreadingHTTPServer((self.host,self.port),H);Thread(target=self.server.serve_forever,daemon=True).start()
 def stop(self):
  if self.server:self.server.shutdown();self.server.server_close();self.server=None
