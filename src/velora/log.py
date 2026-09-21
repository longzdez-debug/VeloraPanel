from __future__ import annotations
import logging,sys
def configure():
 logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s: %(message)s",stream=sys.stdout)
 return logging.getLogger("velora")
