from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
class GsiServer:
    def __init__(self,host,port,token,on_state):self.host=host;self.port=port;self.token=token;self.on_state=on_state;self.server=None
    def serve_forever(self):
        parent=self
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                if self.headers.get("Authorization","")!="Bearer "+parent.token:self.send_response(401);self.end_headers();return
                try:data=json.loads(self.rfile.read(int(self.headers.get("Content-Length","0"))))
                except (ValueError,TypeError):self.send_response(400);self.end_headers();return
                parent.on_state(data);self.send_response(200);self.end_headers()
            def log_message(self,*args):return
        self.server=ThreadingHTTPServer((self.host,self.port),Handler);self.server.serve_forever()
    def shutdown(self):
        if self.server:self.server.shutdown()
