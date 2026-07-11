"""Tests for the World Cup schedule email agent."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from world_cup_email_agent.agent import WorldCupEmailAgent
from world_cup_email_agent.config import AgentConfig
from world_cup_email_agent.emailer import build_email, deliver
from world_cup_email_agent.schedule import (
    Match,
    ScheduleClient,
    filter_upcoming,
    upcoming_in_days,
)


SAMPLE_PAYLOAD = {
    "meta": {"version": "1.0"},
    "count": 3,
    "data": [
        {
            "num": 1,
            "date": "2026-07-11",
            "time_utc": "21:00",
            "datetime_utc": "2026-07-11T21:00:00Z",
            "home_name": "Norway",
            "away_name": "England",
            "group": None,
            "phase": "quarter-finals",
            "venue_name": "AT&T Stadium",
            "venue_city": "Arlington, TX",
            "status": None,
        },
        {
            "num": 2,
            "date": "2026-07-12",
            "time_utc": "01:00",
            "datetime_utc": "2026-07-12T01:00:00Z",
            "home_name": "Argentina",
            "away_name": "Switzerland",
            "phase": "quarter-finals",
            "venue_name": "Hard Rock Stadium",
            "venue_city": "Miami Gardens, FL",
            "status": None,
        },
        {
            "num": 3,
            "date": "2026-07-19",
            "time_utc": "19:00",
            "datetime_utc": "2026-07-19T19:00:00Z",
            "home_name": "TBD",
            "away_name": "TBD",
            "phase": "final",
            "venue_name": "Lumen Field",
            "venue_city": "Seattle, WA",
            "status": None,
        },
        {
            "num": 99,
            "date": "2026-07-09",
            "time_utc": "19:00",
            "datetime_utc": "2026-07-09T19:00:00Z",
            "home_name": "France",
            "away_name": "Brazil",
            "phase": "quarter-finals",
            "venue_name": "MetLife Stadium",
            "venue_city": "East Rutherford, NJ",
            "status": "FINISHED",
            "score_home": 2,
            "score_away": 1,
        },
    ],
}


class FakeClient(ScheduleClient):
    def __init__(self, payload: dict) -> None:
        super().__init__(url="https://example.test/matches.json")
        self._payload = payload

    def fetch_matches(self) -> list[Match]:
        return [
            Match.from_api(row)
            for row in self._payload["data"]
            if isinstance(row, dict)
        ]


class ScheduleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.matches = FakeClient(SAMPLE_PAYLOAD).fetch_matches()
        self.now = datetime(2026, 7, 11, 5, 0, tzinfo=timezone.utc)

    def test_parse_match_fields(self) -> None:
        match = self.matches[0]
        self.assertEqual(match.home, "Norway")
        self.assertEqual(match.phase_label, "Quarter-finals")
        self.assertIn("vs", match.matchup)

    def test_filter_upcoming_skips_finished(self) -> None:
        upcoming = filter_upcoming(self.matches, now=self.now)
        self.assertEqual(len(upcoming), 3)
        self.assertTrue(all(not m.is_finished for m in upcoming))

    def test_upcoming_in_days_window(self) -> None:
        window = upcoming_in_days(
            self.matches, 1, now=self.now, tz_name="Asia/Shanghai"
        )
        # Jul 11 21:00 UTC and Jul 12 01:00 UTC fall within next local day window.
        self.assertGreaterEqual(len(window), 1)
        self.assertTrue(all(m.kickoff_utc >= self.now for m in window))


class EmailAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 7, 11, 5, 0, tzinfo=timezone.utc)

    def test_build_email_contains_matches(self) -> None:
        matches = FakeClient(SAMPLE_PAYLOAD).fetch_matches()
        upcoming = filter_upcoming(matches, now=self.now)
        config = AgentConfig(
            recipient="3461630168@qq.com",
            timezone="Asia/Shanghai",
            dry_run=True,
        )
        draft = build_email(upcoming, config, generated_at=self.now)
        self.assertIn("Norway vs England", draft.text_body)
        self.assertIn("Norway vs England", draft.html_body)
        self.assertEqual(draft.recipient, "3461630168@qq.com")

    def test_dry_run_writes_files(self) -> None:
        matches = FakeClient(SAMPLE_PAYLOAD).fetch_matches()
        upcoming = filter_upcoming(matches, now=self.now)
        with tempfile.TemporaryDirectory() as tmp:
            config = AgentConfig(
                recipient="3461630168@qq.com",
                dry_run=True,
                output_dir=tmp,
            )
            draft = build_email(upcoming, config, generated_at=self.now)
            result = deliver(draft, config)
            self.assertEqual(result.mode, "dry-run")
            self.assertIsNotNone(result.path)
            path = Path(result.path or "")
            self.assertTrue(path.exists())
            self.assertIn("Subject:", path.read_text(encoding="utf-8"))

    def test_agent_run_window(self) -> None:
        config = AgentConfig(
            recipient="3461630168@qq.com",
            dry_run=True,
            output_dir=tempfile.mkdtemp(),
            lookahead_days=7,
            timezone="Asia/Shanghai",
        )
        agent = WorldCupEmailAgent(config=config, client=FakeClient(SAMPLE_PAYLOAD))
        result = agent.run(mode="window", days=10, now=self.now)
        self.assertEqual(result.match_count, 3)
        self.assertEqual(result.delivery.mode, "dry-run")
        self.assertIn("World Cup", result.draft.subject)

    def test_schedule_client_parses_live_shape(self) -> None:
        client = ScheduleClient("https://example.test/matches.json")
        payload_bytes = json.dumps(SAMPLE_PAYLOAD).encode("utf-8")

        class FakeResponse:
            def read(self) -> bytes:
                return payload_bytes

            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *args: object) -> None:
                return None

        with patch("world_cup_email_agent.schedule.urllib.request.urlopen", return_value=FakeResponse()):
            matches = client.fetch_matches()
        self.assertEqual(len(matches), 4)
        by_number = {match.number: match for match in matches}
        self.assertEqual(by_number[1].home, "Norway")
        self.assertEqual(matches[0].kickoff_utc, min(m.kickoff_utc for m in matches))


if __name__ == "__main__":
    unittest.main()
