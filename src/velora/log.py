from __future__ import annotations
import logging,os
def configure_logging(data_dir="data"):
 os.makedirs(data_dir,exist_ok=True)
 logger=logging.getLogger("velora");logger.setLevel(logging.INFO)
 if not logger.handlers:
  h=logging.FileHandler(os.path.join(data_dir,"velora.log"),encoding="utf-8");h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"));logger.addHandler(h)
  logger.addHandler(logging.StreamHandler())
 return logger
