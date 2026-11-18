from __future__ import annotations

import socket

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from piccolo.app import create_app
from piccolo.config import Config


@pytest.fixture
def closed_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = int(sock.getsockname()[1])
    sock.close()
    return port


def test_websockify_proxies_binary_frames(echo_server: int) -> None:
    app = create_app(Config(vnc_host="127.0.0.1", vnc_port=echo_server))

    with TestClient(app) as client, client.websocket_connect("/websockify") as websocket:
        websocket.send_bytes(b"hello-piccolo")
        assert websocket.receive_bytes() == b"hello-piccolo"

        websocket.send_bytes(b"second-frame")
        assert websocket.receive_bytes() == b"second-frame"


def test_websockify_proxies_text_frames_as_bytes(echo_server: int) -> None:
    app = create_app(Config(vnc_host="127.0.0.1", vnc_port=echo_server))

    with TestClient(app) as client, client.websocket_connect("/websockify") as websocket:
        websocket.send_text("hello")
        assert websocket.receive_bytes() == b"hello"


def test_websockify_closes_when_vnc_is_unreachable(closed_port: int) -> None:
    app = create_app(Config(vnc_host="127.0.0.1", vnc_port=closed_port))

    with (
        TestClient(app) as client,
        client.websocket_connect("/websockify") as websocket,
        pytest.raises(WebSocketDisconnect),
    ):
        websocket.receive_bytes()
