"""Runtime configuration for the Piccolo service."""

from __future__ import annotations

from dataclasses import dataclass

LOG_LEVELS = ("critical", "error", "warning", "info", "debug", "trace")


@dataclass(frozen=True, slots=True)
class Config:
    """Configuration shared by the CLI and the FastAPI application."""

    vnc_host: str
    vnc_port: int
    web_host: str = "0.0.0.0"
    web_port: int = 65211
    log_level: str = "info"

    def __post_init__(self) -> None:
        if not self.vnc_host.strip():
            raise ValueError("vnc_host must not be empty")
        if not self.web_host.strip():
            raise ValueError("web_host must not be empty")
        for name in ("vnc_port", "web_port"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 65535:
                raise ValueError(f"{name} must be an integer between 1 and 65535")
        if self.log_level not in LOG_LEVELS:
            raise ValueError(f"unsupported log_level: {self.log_level!r}")
