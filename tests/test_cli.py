from __future__ import annotations

import pytest

from piccolo.cli import parse_config
from piccolo.config import Config


def test_parse_cli_arguments() -> None:
    config = parse_config(["--ip", "192.168.1.10", "--port", "65201"], env={})

    assert config.vnc_host == "192.168.1.10"
    assert config.vnc_port == 65201
    assert config.web_host == "0.0.0.0"
    assert config.web_port == 65211
    assert config.log_level == "info"


def test_environment_fallback() -> None:
    env = {
        "PICCOLO_VNC_HOST": "10.0.0.5",
        "PICCOLO_VNC_PORT": "5901",
        "PICCOLO_WEB_HOST": "127.0.0.1",
        "PICCOLO_WEB_PORT": "8080",
        "PICCOLO_LOG_LEVEL": "DEBUG",
    }

    config = parse_config([], env=env)

    assert config.vnc_host == "10.0.0.5"
    assert config.vnc_port == 5901
    assert config.web_host == "127.0.0.1"
    assert config.web_port == 8080
    assert config.log_level == "debug"


def test_cli_overrides_environment() -> None:
    env = {"PICCOLO_VNC_HOST": "10.0.0.5", "PICCOLO_VNC_PORT": "5901"}

    config = parse_config(["--ip", "192.168.1.20", "--port", "65213"], env=env)

    assert config.vnc_host == "192.168.1.20"
    assert config.vnc_port == 65213


def test_missing_host_and_port_fails() -> None:
    with pytest.raises(SystemExit):
        parse_config([], env={})


def test_invalid_port_fails() -> None:
    with pytest.raises(SystemExit):
        parse_config(["--ip", "127.0.0.1", "--port", "70000"], env={})


def test_invalid_env_port_fails() -> None:
    with pytest.raises(SystemExit):
        parse_config(["--ip", "127.0.0.1"], env={"PICCOLO_VNC_PORT": "not-a-port"})


def test_config_rejects_invalid_ports() -> None:
    with pytest.raises(ValueError):
        Config(vnc_host="127.0.0.1", vnc_port=0)
