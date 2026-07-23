#!/usr/bin/env python3
"""持续轮询官网：发现新岗位立即推送（无固定发送时刻）。外投已关闭。"""

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


def load_config(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise SystemExit("PyYAML required: pip install pyyaml")
        return yaml.safe_load(text) or {}
    import json

    return json.loads(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="新岗位即时推送轮询器")
    parser.add_argument("--config", default=os.environ.get("JOB_OUTREACH_CONFIG"), required=False)
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument(
        "--poll-sec",
        type=int,
        default=None,
        help="轮询间隔秒（默认读 config.schedule.poll_interval_sec，建议 300~900）",
    )
    parser.add_argument("--once", action="store_true", help="只跑一轮后退出")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if not args.config:
        raise SystemExit("请通过 --config 或 JOB_OUTREACH_CONFIG 指定配置")

    cfg = load_config(Path(args.config).expanduser())
    schedule = cfg.get("schedule") or {}
    tz = ZoneInfo(schedule.get("timezone", "Asia/Shanghai"))
    poll = int(args.poll_sec or schedule.get("poll_interval_sec", 600))

    print(f"watcher started tz={tz} poll_interval_sec={poll} (push on new jobs only)")

    while True:
        now = datetime.now(tz)
        print(f"poll at {now.isoformat()}")
        daily_args = ["--config", args.config, "--skill-root", args.skill_root, "--force-schedule"]
        if args.dry_run:
            daily_args.append("--dry-run")
        code = daily_main(daily_args)
        print(f"poll finished exit={code}")
        if args.once:
            return code
        time.sleep(max(60, poll))


if __name__ == "__main__":
    sys.exit(main())
