from pathlib import Path
import json,os
from tempfile import NamedTemporaryFile
class JsonStore:
 def __init__(self,root="data"):self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
 def load(self,name,default):
  try:return json.loads((self.root/f"{name}.json").read_text(encoding="utf-8"))
  except (FileNotFoundError,json.JSONDecodeError):return default
 def save(self,name,value):
  p=self.root/f"{name}.json"
  with NamedTemporaryFile("w",encoding="utf-8",dir=self.root,delete=False) as f:json.dump(value,f,indent=2,ensure_ascii=False);f.flush();os.fsync(f.fileno());tmp=f.name
  os.replace(tmp,p)
