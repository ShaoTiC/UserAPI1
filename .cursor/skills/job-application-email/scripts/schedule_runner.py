#!/usr/bin/env python3
"""工作日定时调度：默认 Asia/Shanghai 09:30 与 14:30。"""

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


def due_slot(now: datetime, morning: str, afternoon: str, window_sec: int) -> str | None:
    """若当前时刻落在某个发送窗口内则返回 slot 名。"""
    for name, hhmm in (("morning", morning), ("afternoon", afternoon)):
        hh, mm = parse_hhmm(hhmm)
        target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        delta = (now - target).total_seconds()
        if 0 <= delta <= window_sec:
            return name
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="求职邮件工作日调度器")
    parser.add_argument("--config", default=os.environ.get("JOB_OUTREACH_CONFIG"), required=False)
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--poll-sec", type=int, default=30, help="轮询间隔秒")
    parser.add_argument("--window-sec", type=int, default=90, help="每个定点的触发窗口秒数")
    parser.add_argument("--once", action="store_true", help="只检查一轮后退出（便于 cron/测试）")
    args = parser.parse_args(argv)

    if not args.config:
        raise SystemExit("请通过 --config 或 JOB_OUTREACH_CONFIG 指定配置")

    cfg = load_config(Path(args.config).expanduser())
    schedule = cfg.get("schedule") or {}
    tz = ZoneInfo(schedule.get("timezone", "Asia/Shanghai"))
    morning = schedule.get("morning", "09:30")
    afternoon = schedule.get("afternoon", "14:30")

    fired: set[str] = set()
    print(f"scheduler started tz={tz} morning={morning} afternoon={afternoon}")

    while True:
        now = datetime.now(tz)
        day = now.strftime("%Y-%m-%d")
        # 新的一天清空 fired
        fired = {k for k in fired if k.startswith(day)}

        if is_workday(now):
            slot = due_slot(now, morning, afternoon, args.window_sec)
            key = f"{day}:{slot}" if slot else ""
            if slot and key not in fired:
                print(f"trigger slot={slot} at {now.isoformat()}")
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
