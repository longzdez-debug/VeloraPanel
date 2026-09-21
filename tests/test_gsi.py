import json
from velora.gsi import GsiServer
def test_server_constructs(): assert GsiServer(token="secret").token=="secret"
