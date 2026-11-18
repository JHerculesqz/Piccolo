"""Command-line interface for Piccolo."""

from __future__ import annotations

import argparse
import os
from collections.abc import Mapping, Sequence

import uvicorn

from . import __version__
from .app import create_app
from .config import LOG_LEVELS, Config

_DEFAULT_WEB_PORT = 65211


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="piccolo",
        description=(
            "Expose a TigerVNC desktop as a browser-accessible cloud computer. "
            "Piccolo serves the noVNC client and proxies WebSocket traffic to TigerVNC."
        ),
    )
    parser.add_argument(
        "--ip",
        dest="vnc_host",
        metavar="HOST",
        help="IP address or hostname of the TigerVNC server (env: PICCOLO_VNC_HOST).",
    )
    parser.add_argument(
        "--port",
        dest="vnc_port",
        metavar="PORT",
        type=int,
        help="TigerVNC port, for example 65212 (env: PICCOLO_VNC_PORT).",
    )
    parser.add_argument(
        "--web-host",
        metavar="HOST",
        help="Bind address for the Piccolo web server (env: PICCOLO_WEB_HOST; default: 0.0.0.0).",
    )
    parser.add_argument(
        "--web-port",
        metavar="PORT",
        type=int,
        help="Port for the noVNC web UI and WebSocket proxy (env: PICCOLO_WEB_PORT; default: 65211).",
    )
    parser.add_argument(
        "--log-level",
        choices=LOG_LEVELS,
        help="Uvicorn log level (env: PICCOLO_LOG_LEVEL; default: info).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def parse_config(
    argv: Sequence[str] | None = None,
    env: Mapping[str, str] | None = None,
) -> Config:
    """Parse CLI arguments with environment-variable fallbacks."""
    parser = build_parser()
    args = parser.parse_args(argv)
    environ = os.environ if env is None else env

    vnc_host = (args.vnc_host or environ.get("PICCOLO_VNC_HOST", "")).strip()
    vnc_port = args.vnc_port if args.vnc_port is not None else _env_int(parser, environ, "PICCOLO_VNC_PORT")
    web_host = (args.web_host or environ.get("PICCOLO_WEB_HOST", "") or "0.0.0.0").strip()
    web_port = (
        args.web_port
        if args.web_port is not None
        else _env_int(parser, environ, "PICCOLO_WEB_PORT", _DEFAULT_WEB_PORT)
    )
    log_level = (args.log_level or environ.get("PICCOLO_LOG_LEVEL", "") or "info").strip().lower()

    if not vnc_host:
        parser.error("--ip is required (or set PICCOLO_VNC_HOST)")
    vnc_port = _require_port(parser, "--port / PICCOLO_VNC_PORT", vnc_port)
    web_port = _require_port(parser, "--web-port / PICCOLO_WEB_PORT", web_port)
    if not web_host:
        parser.error("--web-host / PICCOLO_WEB_HOST must not be empty")
    if log_level not in LOG_LEVELS:
        parser.error(f"--log-level / PICCOLO_LOG_LEVEL must be one of: {', '.join(LOG_LEVELS)}")

    return Config(
        vnc_host=vnc_host,
        vnc_port=vnc_port,
        web_host=web_host,
        web_port=web_port,
        log_level=log_level,
    )


def _env_int(
    parser: argparse.ArgumentParser,
    env: Mapping[str, str],
    name: str,
    default: int | None = None,
) -> int | None:
    raw = env.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        parser.error(f"{name} must be an integer, got {raw!r}")
        raise


def _require_port(parser: argparse.ArgumentParser, label: str, value: int | None) -> int:
    if value is None:
        parser.error(f"{label} is required")
    if not 1 <= value <= 65535:
        parser.error(f"{label} must be between 1 and 65535")
    return value


def _print_banner(config: Config) -> None:
    display_host = "127.0.0.1" if config.web_host in {"0.0.0.0", "::"} else config.web_host
    if ":" in display_host and not display_host.startswith("["):
        display_host = f"[{display_host}]"
    print(f"Piccolo {__version__}")
    print(f"  Web UI : http://{display_host}:{config.web_port}/vnc.html?autoconnect=true")
    print(f"  VNC    : {config.vnc_host}:{config.vnc_port}")
    print(f"  Listen : {config.web_host}:{config.web_port}")


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point for the ``piccolo`` command."""
    config = parse_config(argv)
    _print_banner(config)
    app = create_app(config)
    uvicorn.run(
        app,
        host=config.web_host,
        port=config.web_port,
        log_level=config.log_level,
    )


if __name__ == "__main__":
    main()
