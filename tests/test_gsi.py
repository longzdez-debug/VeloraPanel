import json
from velora.gsi import GsiServer
def test_server_constructs(): assert GsiServer(token="secret").token=="secret"


def test_gsi_rejects_malformed_json_and_invalid_token():
    import threading
    from http.client import HTTPConnection
    server = GsiServer(host="127.0.0.1", port=0, token="secret")
    # The production server binds the configured port; use an ephemeral free
    # port selected by the OS, then replace the server port before start.
    import socket
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server.port = port
    server.start()
    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=2)
        conn.request("POST", "/", body=b"not-json", headers={"Content-Length":"8"})
        assert conn.getresponse().status == 400
        conn.close()

        conn = HTTPConnection("127.0.0.1", port, timeout=2)
        body = json.dumps({"auth":{"token":"wrong"}}).encode()
        conn.request("POST", "/", body=body)
        assert conn.getresponse().status == 401
        conn.close()
    finally:
        server.stop()


def test_gsi_callback_exception_does_not_break_endpoint():
    import socket
    from http.client import HTTPConnection
    server = GsiServer(host="127.0.0.1", port=0)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server.port = port
    server.on_snapshot(lambda snap: (_ for _ in ()).throw(RuntimeError("boom")))
    server.start()
    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=2)
        body = json.dumps({"provider":{"timestamp":1},"map":{"name":"de_dust2","phase":"live","round":1},"round":{"phase":"live"},"player":{"steamid":"1","activity":"playing","state":{"health":100}}}).encode()
        conn.request("POST", "/", body=body)
        assert conn.getresponse().status == 204
        conn.close()
    finally:
        server.stop()
