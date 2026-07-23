#!/usr/bin/env python3
"""调度器：默认工作日触发每日岗位摘要；可选保留 outreach 时段。"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from run_daily import main as daily_main
from send_batch import is_workday, main as send_main


def load_config(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise SystemExit("PyYAML required: pip install pyyaml")
        return yaml.safe_load(text) or {}
    import json

    return json.loads(text)


def parse_hhmm(value: str) -> tuple[int, int]:
    hh, mm = value.strip().split(":")
    return int(hh), int(mm)


def due_slot(now: datetime, name: str, hhmm: str, window_sec: int) -> bool:
    hh, mm = parse_hhmm(hhmm)
    target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    delta = (now - target).total_seconds()
    return 0 <= delta <= window_sec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="求职 skill 调度器（摘要优先）")
    parser.add_argument("--config", default=os.environ.get("JOB_OUTREACH_CONFIG"), required=False)
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--poll-sec", type=int, default=30)
    parser.add_argument("--window-sec", type=int, default=90)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)

    if not args.config:
        raise SystemExit("请通过 --config 或 JOB_OUTREACH_CONFIG 指定配置")

    cfg = load_config(Path(args.config).expanduser())
    schedule = cfg.get("schedule") or {}
    tz = ZoneInfo(schedule.get("timezone", "Asia/Shanghai"))
    digest_at = schedule.get("digest_time", "09:00")
    enable_outreach = bool(schedule.get("enable_outreach_slots", False))
    morning = schedule.get("morning", "09:30")
    afternoon = schedule.get("afternoon", "14:30")

    fired: set[str] = set()
    print(
        f"scheduler started tz={tz} digest={digest_at} "
        f"outreach_slots={enable_outreach}"
    )

    while True:
        now = datetime.now(tz)
        day = now.strftime("%Y-%m-%d")
        fired = {k for k in fired if k.startswith(day)}

        if is_workday(now):
            if due_slot(now, "digest", digest_at, args.window_sec):
                key = f"{day}:digest"
                if key not in fired:
                    print(f"trigger digest at {now.isoformat()}")
                    code = daily_main(
                        ["--config", args.config, "--skill-root", args.skill_root]
                    )
                    fired.add(key)
                    print(f"digest finished exit={code}")

            if enable_outreach:
                for slot, hhmm in (("morning", morning), ("afternoon", afternoon)):
                    if due_slot(now, slot, hhmm, args.window_sec):
                        key = f"{day}:{slot}"
                        if key not in fired:
                            print(f"trigger outreach slot={slot}")
                            code = send_main(
                                [
                                    "--config",
                                    args.config,
                                    "--skill-root",
                                    args.skill_root,
                                    "--slot",
                                    slot,
                                ]
                            )
                            fired.add(key)
                            print(f"slot={slot} finished exit={code}")
        else:
            print(f"NOT_WORKDAY skip {now.isoformat()}")

        if args.once:
            return 0
        time.sleep(max(5, args.poll_sec))


if __name__ == "__main__":
    sys.exit(main())
