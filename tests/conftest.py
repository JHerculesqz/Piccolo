from __future__ import annotations

import socketserver
import threading
from collections.abc import Iterator

import pytest


class _EchoHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        try:
            while True:
                data = self.request.recv(65536)
                if not data:
                    return
                self.request.sendall(data)
        except OSError:
            return


class _EchoServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


@pytest.fixture
def echo_server() -> Iterator[int]:
    """A local TCP echo server that stands in for TigerVNC."""
    server = _EchoServer(("127.0.0.1", 0), _EchoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield int(server.server_address[1])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
