#!/usr/bin/env python3
"""批量求职邮件发送入口：安全检查 → 选址 → 发送 → 写状态/报告。"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from check_security import FIXED_INTRO, main as security_main
from lib_mail import send_one

WORKDAYS = {0, 1, 2, 3, 4}  # Mon-Fri


def load_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise SystemExit("PyYAML required: pip install pyyaml")
        return yaml.safe_load(text) or {}
    return json.loads(text)


def resolve(path_str: str | None, base: Path) -> Path | None:
    if not path_str:
        return None
    p = Path(os.path.expanduser(path_str))
    if not p.is_absolute():
        p = (base / p).resolve()
    return p


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"records": {}, "daily": {}}
    raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        bak = path.with_suffix(".json.bak")
        raise SystemExit(f"STATE_CORRUPT: {exc}; try restore from {bak}") from exc
    data.setdefault("records", {})
    data.setdefault("daily", {})
    return data


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, path.with_suffix(".json.bak"))
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def read_companies(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def build_body(cfg: dict[str, Any], intro_path: Path | None) -> str:
    if intro_path and intro_path.exists():
        intro = intro_path.read_text(encoding="utf-8").strip()
    else:
        intro = FIXED_INTRO
    if intro != FIXED_INTRO:
        raise SystemExit("INTRO_MISMATCH: refuse to send altered self-intro")
    closing = ((cfg.get("email") or {}).get("closing") or "").strip()
    return intro if not closing else f"{intro}\n\n{closing}"


def is_workday(now: datetime) -> bool:
    return now.weekday() in WORKDAYS


def daily_count(state: dict[str, Any], day_key: str) -> int:
    return int((state.get("daily") or {}).get(day_key, 0))


def select_targets(
    rows: list[dict[str, str]],
    state: dict[str, Any],
    *,
    limit: int,
    retry_failed: bool,
    force: bool,
) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    for row in rows:
        cid = (row.get("company_id") or "").strip()
        email = (row.get("email") or "").strip()
        key = f"{cid}|{email}"
        rec = (state.get("records") or {}).get(key, {})
        status = rec.get("status")
        if status == "invalid":
            continue
        if status == "sent" and not force:
            continue
        if retry_failed:
            if status in {"failed", "deferred"}:
                selected.append(row)
        else:
            if status in {None, "pending", "failed", "deferred"} or force:
                selected.append(row)
        if len(selected) >= limit:
            break
    return selected


def render_report(template: str, ctx: dict[str, Any]) -> str:
    out = template
    for k, v in ctx.items():
        out = out.replace(f"{{{{{k}}}}}", str(v))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="批量发送求职邮件")
    parser.add_argument("--config", default=os.environ.get("JOB_OUTREACH_CONFIG"), required=False)
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--slot", choices=["morning", "afternoon", "manual"], default="manual")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--force", action="store_true", help="允许重发已 sent")
    parser.add_argument("--force-schedule", action="store_true", help="忽略工作日检查")
    parser.add_argument("--skip-security", action="store_true", help="仅测试用，生产禁止")
    args = parser.parse_args(argv)

    if not args.config:
        raise SystemExit("请通过 --config 或环境变量 JOB_OUTREACH_CONFIG 指定配置文件")

    skill_root = Path(args.skill_root).resolve()
    cfg_path = Path(args.config).expanduser()
    cfg = load_config(cfg_path)

    if not args.skip_security and not args.dry_run:
        code = security_main(
            ["--config", str(cfg_path), "--skill-root", str(skill_root), "--mode", "outreach"]
        )
        if code != 0:
            return code

    tz_name = (cfg.get("schedule") or {}).get("timezone", "Asia/Shanghai")
    now = datetime.now(ZoneInfo(tz_name))
    if not args.force_schedule and args.slot in {"morning", "afternoon"} and not is_workday(now):
        print(f"NOT_WORKDAY: {now.isoformat()} skipped")
        return 0

    paths = cfg.get("paths") or {}
    companies_path = resolve(paths.get("companies"), skill_root)
    resume_path = resolve(paths.get("resume"), skill_root)
    intro_path = resolve(paths.get("self_intro"), skill_root) or (skill_root / "assets" / "self_intro.txt")
    state_path = resolve(paths.get("state"), skill_root) or Path.home() / ".job-outreach" / "state.json"
    report_dir = resolve((cfg.get("report") or {}).get("dir"), skill_root) or (
        Path.home() / ".job-outreach" / "reports"
    )
    template_path = skill_root / "assets" / "report_template.md"

    if companies_path is None or resume_path is None:
        raise SystemExit("CONFIG_INVALID: paths.companies / paths.resume required")

    batch_size = int(args.limit or (cfg.get("schedule") or {}).get("batch_size", 5))
    daily_limit = int((cfg.get("security") or {}).get("daily_send_limit", 40))
    min_interval = float((cfg.get("mail") or {}).get("min_interval_sec", 8))

    state = load_state(state_path)
    day_key = now.strftime("%Y-%m-%d")
    already = daily_count(state, day_key)
    remaining_today = max(0, daily_limit - already)
    if remaining_today <= 0 and not args.dry_run:
        print("SECURITY_BLOCKED: daily_send_limit reached")
        return 2

    rows = read_companies(companies_path)
    targets = select_targets(
        rows,
        state,
        limit=min(batch_size, remaining_today if not args.dry_run else batch_size),
        retry_failed=args.retry_failed,
        force=args.force,
    )

    body = build_body(cfg, intro_path)
    email_cfg = cfg.get("email") or {}
    subject = email_cfg.get("subject", "求职-Java开发实习生-邵俊凯-东北农业大学")
    from_name = email_cfg.get("from_name", "邵俊凯")
    attach_name = email_cfg.get("attachment_filename", "邵俊凯-Java开发实习生-简历.pdf")

    results: list[dict[str, Any]] = []
    success = fail = skip = 0
    auth_circuit_open = False

    for idx, row in enumerate(targets):
        if auth_circuit_open:
            skip += 1
            continue
        cid = (row.get("company_id") or "").strip()
        email = (row.get("email") or "").strip()
        key = f"{cid}|{email}"
        company_name = (row.get("company_name") or "").strip()

        result = send_one(
            cfg.get("mail") or {},
            to_email=email,
            subject=subject,
            body=body,
            resume_path=resume_path,
            from_name=from_name,
            attach_name=attach_name,
            dry_run=args.dry_run,
        )

        record = {
            "company_id": cid,
            "company_name": company_name,
            "email": email,
            "slot": args.slot,
            "code": result.code,
            "message": result.message,
            "attempts": result.attempts,
            "at": now.isoformat(),
        }
        results.append(record)

        if args.dry_run:
            skip += 1
            print(f"DRY_RUN {company_name} <{email}>")
            continue

        rec = state["records"].setdefault(key, {})
        if result.ok:
            rec.update({"status": "sent", "last_success_at": now.isoformat(), "last_error": None})
            state["daily"][day_key] = daily_count(state, day_key) + 1
            success += 1
            print(f"OK {company_name} <{email}> attempts={result.attempts}")
        else:
            status = "invalid" if result.code == "INVALID_RECIPIENT" else "failed"
            if result.code == "RATE_LIMITED":
                status = "deferred"
            rec.update(
                {
                    "status": status,
                    "last_error": f"{result.code}: {result.message}",
                    "last_failed_at": now.isoformat(),
                }
            )
            fail += 1
            print(f"FAIL {company_name} <{email}> {result.code}: {result.message}")
            if result.code == "AUTH_FAILED":
                auth_circuit_open = True
                print("AUTH_FAILED circuit open: abort remaining batch")

        save_state(state_path, state)
        if idx < len(targets) - 1 and not args.dry_run:
            time.sleep(min_interval)

    # 报告
    report_dir.mkdir(parents=True, exist_ok=True)
    template = template_path.read_text(encoding="utf-8") if template_path.exists() else "# Report\n"
    lines = []
    for r in results:
        lines.append(
            f"| {r['company_name']} | {r['email']} | {r['code']} | {r['attempts']} | {r['message'][:80]} |"
        )
    report = render_report(
        template,
        {
            "date": day_key,
            "slot": args.slot,
            "timezone": tz_name,
            "success_count": success,
            "fail_count": fail,
            "skip_count": skip,
            "total_count": len(targets),
            "dry_run": args.dry_run,
            "result_rows": "\n".join(lines) if lines else "| (empty) | - | - | - | - |",
            "generated_at": datetime.now(ZoneInfo(tz_name)).isoformat(),
        },
    )
    report_path = report_dir / f"report-{day_key}-{args.slot}.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"Report written: {report_path}")

    if fail and success == 0 and not args.dry_run:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
