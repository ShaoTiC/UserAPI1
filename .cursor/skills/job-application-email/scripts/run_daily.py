#!/usr/bin/env python3
"""每日主入口：采集岗位 → 发送摘要到用户邮箱。"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from collect_jobs import main as collect_main
from send_digest import main as digest_main


WORKDAYS = {0, 1, 2, 3, 4}


def load_config(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise SystemExit("PyYAML required")
        return yaml.safe_load(text) or {}
    import json

    return json.loads(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="每日招聘速递流水线")
    parser.add_argument("--config", default=os.environ.get("JOB_OUTREACH_CONFIG"), required=False)
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force-schedule", action="store_true", help="忽略工作日限制")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--skip-security", action="store_true")
    parser.add_argument("--force", action="store_true", help="强制重发今日摘要")
    args = parser.parse_args(argv)

    if not args.config:
        raise SystemExit("请通过 --config 或 JOB_OUTREACH_CONFIG 指定配置")

    cfg = load_config(Path(args.config).expanduser())
    tz = ZoneInfo((cfg.get("schedule") or {}).get("timezone", "Asia/Shanghai"))
    now = datetime.now(tz)
    if not args.force_schedule and now.weekday() not in WORKDAYS:
        print(f"NOT_WORKDAY: {now.isoformat()} skipped")
        return 0

    collect_args = ["--config", args.config, "--skill-root", args.skill_root]
    rc = collect_main(collect_args)
    if rc != 0:
        print(f"collect_jobs exit={rc} （若已有部分结果仍尝试发送）")

    digest_args = ["--config", args.config, "--skill-root", args.skill_root]
    if args.dry_run:
        digest_args.append("--dry-run")
    if args.skip_security:
        digest_args.append("--skip-security")
    if args.force:
        digest_args.append("--force")
    if args.limit is not None:
        digest_args.extend(["--limit", str(args.limit)])
    return digest_main(digest_args)


if __name__ == "__main__":
    sys.exit(main())
