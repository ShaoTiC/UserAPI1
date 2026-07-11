"""Orchestrate schedule fetch, filtering, and email delivery."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from .config import AgentConfig
from .emailer import DeliveryResult, EmailDraft, build_email, deliver
from .schedule import Match, ScheduleClient, filter_upcoming, upcoming_in_days

Mode = Literal["upcoming", "window", "all-remaining"]


@dataclass(frozen=True)
class AgentRunResult:
    """Summary of one agent execution."""

    mode: Mode
    match_count: int
    matches: list[Match]
    draft: EmailDraft
    delivery: DeliveryResult


class WorldCupEmailAgent:
    """Agent that emails World Cup fixtures on demand or on a schedule."""

    def __init__(
        self,
        config: AgentConfig | None = None,
        client: ScheduleClient | None = None,
    ) -> None:
        self.config = config or AgentConfig.from_env()
        self.client = client or ScheduleClient(self.config.schedule_url)

    def run(
        self,
        mode: Mode = "window",
        *,
        days: int | None = None,
        now: datetime | None = None,
    ) -> AgentRunResult:
        matches = self.client.fetch_matches()
        selected = self.select_matches(matches, mode=mode, days=days, now=now)
        title = self._title_for(mode, selected, days=days or self.config.lookahead_days)
        draft = build_email(selected, self.config, title=title, generated_at=now)
        delivery = deliver(draft, self.config)
        return AgentRunResult(
            mode=mode,
            match_count=len(selected),
            matches=list(selected),
            draft=draft,
            delivery=delivery,
        )

    def select_matches(
        self,
        matches: list[Match],
        *,
        mode: Mode,
        days: int | None = None,
        now: datetime | None = None,
    ) -> list[Match]:
        current = now or datetime.now(timezone.utc)
        if mode == "all-remaining":
            return filter_upcoming(matches, now=current)
        if mode == "upcoming":
            # Alias for remaining tournament fixtures.
            return filter_upcoming(matches, now=current)
        window_days = self.config.lookahead_days if days is None else days
        return upcoming_in_days(
            matches,
            window_days,
            now=current,
            tz_name=self.config.timezone,
        )

    def run_forever(self, *, interval_hours: float = 24.0, mode: Mode = "window") -> None:
        """Loop forever, sending one digest every ``interval_hours``."""

        seconds = max(interval_hours, 0.1) * 3600
        while True:
            result = self.run(mode=mode)
            print(
                f"[{datetime.now(timezone.utc).isoformat()}] "
                f"{result.delivery.mode}: {result.match_count} matches → "
                f"{result.delivery.recipient}"
                + (f" ({result.delivery.path})" if result.delivery.path else "")
            )
            time.sleep(seconds)

    @staticmethod
    def _title_for(mode: Mode, matches: list[Match], *, days: int) -> str | None:
        if not matches:
            return "FIFA World Cup 2026 — no upcoming matches"
        if mode == "window":
            return f"FIFA World Cup 2026 — next {days} day(s)"
        return "FIFA World Cup 2026 — remaining matches"


def run_once(
    config: AgentConfig | None = None,
    *,
    mode: Mode = "window",
    days: int | None = None,
) -> AgentRunResult:
    """Convenience wrapper used by the CLI and tests."""

    return WorldCupEmailAgent(config=config).run(mode=mode, days=days)
