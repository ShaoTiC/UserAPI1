"""Fetch and filter FIFA World Cup 2026 match schedules."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable, Sequence
from zoneinfo import ZoneInfo

from .config import DEFAULT_SCHEDULE_URL

PHASE_LABELS = {
    "group": "Group Stage",
    "last-32": "Round of 32",
    "round-of-16": "Round of 16",
    "quarter-finals": "Quarter-finals",
    "semi-finals": "Semi-finals",
    "third-place-play-off": "Third-place Play-off",
    "final": "Final",
}


@dataclass(frozen=True)
class Match:
    """A single World Cup fixture."""

    number: int
    kickoff_utc: datetime
    home: str
    away: str
    phase: str
    group: str | None
    venue: str
    city: str
    status: str | None
    score_home: int | None = None
    score_away: int | None = None
    slug: str = ""

    @property
    def phase_label(self) -> str:
        label = PHASE_LABELS.get(self.phase, self.phase.replace("-", " ").title())
        if self.phase == "group" and self.group:
            return f"{label} · Group {self.group}"
        return label

    @property
    def is_finished(self) -> bool:
        status = (self.status or "").upper()
        return status in {"FINISHED", "FT", "AET", "PEN"}

    @property
    def matchup(self) -> str:
        home = self.home or "TBD"
        away = self.away or "TBD"
        return f"{home} vs {away}"

    def local_kickoff(self, tz_name: str) -> datetime:
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = timezone.utc
        return self.kickoff_utc.astimezone(tz)

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> "Match":
        kickoff = _parse_utc(str(raw.get("datetime_utc") or ""))
        if kickoff is None:
            date_part = str(raw.get("date") or "1970-01-01")
            time_part = str(raw.get("time_utc") or "00:00")
            kickoff = _parse_utc(f"{date_part}T{time_part}:00Z") or datetime(
                1970, 1, 1, tzinfo=timezone.utc
            )

        return cls(
            number=int(raw.get("num") or 0),
            kickoff_utc=kickoff,
            home=str(raw.get("home_name") or raw.get("home") or "").strip() or "TBD",
            away=str(raw.get("away_name") or raw.get("away") or "").strip() or "TBD",
            phase=str(raw.get("phase") or "unknown"),
            group=(str(raw["group"]) if raw.get("group") else None),
            venue=str(raw.get("venue_name") or raw.get("venue") or "TBD"),
            city=str(raw.get("venue_city") or ""),
            status=(str(raw["status"]) if raw.get("status") is not None else None),
            score_home=_as_optional_int(raw.get("score_home")),
            score_away=_as_optional_int(raw.get("score_away")),
            slug=str(raw.get("slug") or ""),
        )


class ScheduleClient:
    """HTTP client for the public World Cup schedule JSON feed."""

    def __init__(self, url: str = DEFAULT_SCHEDULE_URL, timeout: float = 30.0) -> None:
        self.url = url
        self.timeout = timeout

    def fetch_matches(self) -> list[Match]:
        payload = self._get_json(self.url)
        rows = payload.get("data") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise ValueError("Unexpected schedule payload: missing match list")
        matches = [Match.from_api(row) for row in rows if isinstance(row, dict)]
        return sorted(matches, key=lambda m: (m.kickoff_utc, m.number))

    def _get_json(self, url: str) -> Any:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "WorldCupEmailAgent/1.0 (+https://github.com/ShaoTiC/UserAPI1)",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Failed to fetch schedule from {url}: {exc}") from exc
        return json.loads(body)


def filter_upcoming(
    matches: Sequence[Match],
    *,
    now: datetime | None = None,
    include_finished: bool = False,
) -> list[Match]:
    """Return matches that kick off at or after ``now``."""

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    selected: list[Match] = []
    for match in matches:
        if not include_finished and match.is_finished:
            continue
        if match.kickoff_utc >= current:
            selected.append(match)
    return selected


def filter_window(
    matches: Sequence[Match],
    *,
    start: datetime,
    end: datetime,
    include_finished: bool = False,
) -> list[Match]:
    """Return matches whose kickoff falls in ``[start, end)``."""

    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    selected: list[Match] = []
    for match in matches:
        if not include_finished and match.is_finished:
            continue
        if start <= match.kickoff_utc < end:
            selected.append(match)
    return selected


def upcoming_in_days(
    matches: Sequence[Match],
    days: int,
    *,
    now: datetime | None = None,
    tz_name: str = "UTC",
) -> list[Match]:
    """Upcoming fixtures within the next ``days`` (rolling window from ``now``).

    ``tz_name`` is reserved for callers that also render local times; the
    selection window is a rolling duration from ``now``.
    """

    _ = tz_name
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    end = current + timedelta(days=max(days, 0))
    return filter_window(matches, start=current, end=end)


def group_by_local_date(
    matches: Iterable[Match], tz_name: str
) -> list[tuple[date, list[Match]]]:
    """Group matches by local calendar date, preserving kickoff order."""

    buckets: dict[date, list[Match]] = {}
    order: list[date] = []
    for match in matches:
        local_day = match.local_kickoff(tz_name).date()
        if local_day not in buckets:
            buckets[local_day] = []
            order.append(local_day)
        buckets[local_day].append(match)
    return [(day, buckets[day]) for day in order]


def _parse_utc(value: str) -> datetime | None:
    if not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _as_optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
