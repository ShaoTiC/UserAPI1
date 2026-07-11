"""Configuration for the World Cup email agent."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_SCHEDULE_URL = "https://wheniskickoff.com/data/v1/matches.json"
DEFAULT_RECIPIENT = "3461630168@qq.com"
DEFAULT_SENDER_NAME = "World Cup Schedule Agent"


@dataclass(frozen=True)
class AgentConfig:
    """Runtime settings loaded from environment variables and CLI flags."""

    recipient: str = DEFAULT_RECIPIENT
    sender_email: str = ""
    sender_name: str = DEFAULT_SENDER_NAME
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_ssl: bool = True
    schedule_url: str = DEFAULT_SCHEDULE_URL
    timezone: str = "Asia/Shanghai"
    lookahead_days: int = 3
    dry_run: bool = True
    output_dir: str = "out"

    @classmethod
    def from_env(cls, **overrides: object) -> "AgentConfig":
        """Build config from environment variables, then apply overrides."""

        def _bool(name: str, default: bool) -> bool:
            raw = os.getenv(name)
            if raw is None:
                return default
            return raw.strip().lower() in {"1", "true", "yes", "on"}

        def _int(name: str, default: int) -> int:
            raw = os.getenv(name)
            if raw is None or not raw.strip():
                return default
            return int(raw)

        values: dict[str, object] = {
            "recipient": os.getenv("WC_EMAIL_TO", DEFAULT_RECIPIENT),
            "sender_email": os.getenv("WC_EMAIL_FROM", os.getenv("SMTP_USERNAME", "")),
            "sender_name": os.getenv("WC_SENDER_NAME", DEFAULT_SENDER_NAME),
            "smtp_host": os.getenv("SMTP_HOST", ""),
            "smtp_port": _int("SMTP_PORT", 465),
            "smtp_username": os.getenv("SMTP_USERNAME", ""),
            "smtp_password": os.getenv("SMTP_PASSWORD", ""),
            "smtp_use_ssl": _bool("SMTP_USE_SSL", True),
            "schedule_url": os.getenv("WC_SCHEDULE_URL", DEFAULT_SCHEDULE_URL),
            "timezone": os.getenv("WC_TIMEZONE", "Asia/Shanghai"),
            "lookahead_days": _int("WC_LOOKAHEAD_DAYS", 3),
            "dry_run": _bool("WC_DRY_RUN", True),
            "output_dir": os.getenv("WC_OUTPUT_DIR", "out"),
        }
        values.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**values)  # type: ignore[arg-type]

    @property
    def can_send(self) -> bool:
        """True when SMTP credentials are present and dry-run is off."""

        return (
            not self.dry_run
            and bool(self.smtp_host)
            and bool(self.smtp_username)
            and bool(self.smtp_password)
            and bool(self.sender_email or self.smtp_username)
            and bool(self.recipient)
        )
