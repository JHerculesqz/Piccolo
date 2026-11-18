from __future__ import annotations

from fastapi.testclient import TestClient

from piccolo import __version__
from piccolo.app import NOVNC_URL, create_app
from piccolo.config import Config


def make_client(vnc_port: int = 5900) -> TestClient:
    return TestClient(create_app(Config(vnc_host="127.0.0.1", vnc_port=vnc_port)))


def test_health() -> None:
    with make_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "piccolo",
        "version": __version__,
    }


def test_root_redirects_to_novnc() -> None:
    with make_client() as client:
        response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == NOVNC_URL


def test_novnc_assets_are_served() -> None:
    with make_client() as client:
        html = client.get("/vnc.html")
        script = client.get("/app/ui.js")
        core = client.get("/core/rfb.js")

    assert html.status_code == 200
    assert "noVNC" in html.text
    assert script.status_code == 200
    assert script.headers["content-type"].split(";")[0] in {"application/javascript", "text/javascript"}
    assert core.status_code == 200
