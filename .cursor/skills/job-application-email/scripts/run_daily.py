#!/usr/bin/env python3
"""一轮流水线：采集 → 若有全新岗位则立即推送。"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from collect_jobs import main as collect_main
from send_digest import main as digest_main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="新岗位速递单轮流水线")
    parser.add_argument("--config", default=os.environ.get("JOB_OUTREACH_CONFIG"), required=False)
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force-schedule", action="store_true", help="兼容旧参数（已忽略，任何时间可跑）")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--skip-security", action="store_true")
    parser.add_argument("--force", action="store_true", help="兼容旧参数（已忽略）")
    args = parser.parse_args(argv)

    if not args.config:
        raise SystemExit("请通过 --config 或 JOB_OUTREACH_CONFIG 指定配置")

    collect_args = ["--config", args.config, "--skill-root", args.skill_root]
    rc = collect_main(collect_args)
    if rc != 0:
        print(f"collect_jobs exit={rc} （若已有部分结果仍尝试发送）")

    digest_args = ["--config", args.config, "--skill-root", args.skill_root]
    if args.dry_run:
        digest_args.append("--dry-run")
    if args.skip_security:
        digest_args.append("--skip-security")
    if args.limit is not None:
        digest_args.extend(["--limit", str(args.limit)])
    return digest_main(digest_args)


if __name__ == "__main__":
    sys.exit(main())
