from dataclasses import dataclass
import os
@dataclass(frozen=True)
class Config:
 gsi_host:str="127.0.0.1";gsi_port:int=27100;gsi_token:str="";tick_hz:float=20;dashboard_host:str="127.0.0.1";dashboard_port:int=8765;data_dir:str="data"
 @classmethod
 def from_env(cls):
  return cls(os.getenv("VELORA_GSI_HOST","127.0.0.1"),int(os.getenv("VELORA_GSI_PORT","27100")),os.getenv("VELORA_GSI_TOKEN",""),float(os.getenv("VELORA_TICK_HZ","20")),os.getenv("VELORA_DASHBOARD_HOST","127.0.0.1"),int(os.getenv("VELORA_DASHBOARD_PORT","8765")),os.getenv("VELORA_DATA_DIR","data"))
