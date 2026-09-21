from __future__ import annotations
import json,os,tempfile
class JsonStore:
 def __init__(self,path): self.path=path
 def load(self,default=None):
  try:
   with open(self.path,encoding="utf-8") as f:return json.load(f)
  except (FileNotFoundError,json.JSONDecodeError):return default
 def save(self,value):
  os.makedirs(os.path.dirname(self.path) or ".",exist_ok=True)
  fd,tmp=tempfile.mkstemp(prefix=".velora-",dir=os.path.dirname(self.path) or ".")
  try:
   with os.fdopen(fd,"w",encoding="utf-8") as f:
    json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
   os.replace(tmp,self.path)
  finally:
   if os.path.exists(tmp):os.unlink(tmp)
