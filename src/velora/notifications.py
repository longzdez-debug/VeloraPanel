from __future__ import annotations
import json
from urllib.request import Request,urlopen

class TelegramNotifier:
    def __init__(self,token="",chat_id=""): self.token=token;self.chat_id=chat_id
    def send(self,text):
        if not self.token or not self.chat_id:return False
        body=json.dumps({"chat_id":self.chat_id,"text":text}).encode()
        req=Request(f"https://api.telegram.org/bot{self.token}/sendMessage",data=body,headers={"Content-Type":"application/json"})
        try:
            with urlopen(req,timeout=5): return True
        except Exception:return False
