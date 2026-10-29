"""FastAPI application for Piccolo."""

from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import Config
from .proxy import proxy_websocket

WEB_ROOT = Path(__file__).resolve().parent / "web" / "vncs"
NOVNC_URL = "/vnc.html?autoconnect=true"

# Windows may map .js to text/plain; make sure browsers load noVNC correctly.
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")


def create_app(config: Config) -> FastAPI:
    """Build the Piccolo FastAPI application."""
    if not (WEB_ROOT / "vnc.html").is_file():
        raise RuntimeError(f"noVNC assets not found under {WEB_ROOT}")

    app = FastAPI(
        title="Piccolo",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.config = config

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url=NOVNC_URL, status_code=307)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "piccolo", "version": __version__}

    @app.websocket("/websockify")
    async def websockify(websocket: WebSocket) -> None:
        await proxy_websocket(websocket, config.vnc_host, config.vnc_port)

    app.mount("/", StaticFiles(directory=str(WEB_ROOT), html=True), name="novnc")
    return app
