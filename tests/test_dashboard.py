from velora.config import Config
from velora.dashboard import Dashboard
from velora.supervisor import Supervisor
def test_dashboard_constructs():
 s=Supervisor(Config());d=Dashboard(s);assert d.host=="127.0.0.1"
