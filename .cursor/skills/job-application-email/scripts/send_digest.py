#!/usr/bin/env python3
"""将新岗位摘要发送到用户自己的邮箱（默认每日约 10 条）。"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from check_security import main as security_main
from lib_mail import send_text


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
        return {"seen_jobs": {}, "digest_daily": {}, "records": {}, "daily": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("seen_jobs", {})
    data.setdefault("digest_daily", {})
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


def render_digest(jobs: list[dict[str, Any]], *, day: str, user_note: str) -> tuple[str, str]:
    lines = [
        f"【每日招聘速递】{day}",
        "",
        f"今日为你筛选出 {len(jobs)} 条较新/匹配的岗位，请尽快查阅并投递。",
        "",
    ]
    if user_note:
        lines.extend([user_note, ""])
    html = [
        f"<h2>【每日招聘速递】{day}</h2>",
        f"<p>今日为你筛选出 <b>{len(jobs)}</b> 条较新/匹配的岗位，请尽快查阅并投递。</p>",
    ]
    if user_note:
        html.append(f"<p>{user_note}</p>")
    html.append("<ol>")
    for i, job in enumerate(jobs, 1):
        title = job.get("title") or "(无标题)"
        company = job.get("company_name") or job.get("company_id") or ""
        url = job.get("url") or ""
        loc = job.get("location") or ""
        pub = job.get("published") or ""
        snippet = job.get("snippet") or ""
        meta = " | ".join(x for x in [company, loc, pub] if x)
        lines.append(f"{i}. {title}")
        if meta:
            lines.append(f"   {meta}")
        lines.append(f"   链接: {url}")
        if snippet:
            lines.append(f"   摘要: {snippet}")
        lines.append("")
        html.append("<li>")
        html.append(f'<p><b><a href="{url}">{title}</a></b><br/>{meta}</p>')
        if snippet:
            html.append(f"<p>{snippet}</p>")
        html.append("</li>")
    html.append("</ol>")
    html.append("<p style='color:#666'>本邮件由 job-application-email skill 自动生成。</p>")
    lines.append("— 由 job-application-email skill 自动生成")
    return "\n".join(lines), "\n".join(html)


def pick_jobs(payload: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    new_jobs = list(payload.get("new_jobs") or [])
    known_jobs = list(payload.get("known_jobs") or [])
    # 优先全新岗位；不足时用已知岗位补齐（仍受日限额）
    selected = new_jobs[:limit]
    if len(selected) < limit:
        selected.extend(known_jobs[: limit - len(selected)])
    return selected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="发送每日岗位摘要到用户邮箱")
    parser.add_argument("--config", default=os.environ.get("JOB_OUTREACH_CONFIG"), required=False)
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--jobs-json", help="collect_jobs 输出的 JSON；默认读当日 cache")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="覆盖 digest.daily_job_limit")
    parser.add_argument("--skip-security", action="store_true")
    parser.add_argument("--force", action="store_true", help="即使今日已发送也再发")
    args = parser.parse_args(argv)

    if not args.config:
        raise SystemExit("请通过 --config 或 JOB_OUTREACH_CONFIG 指定配置")

    skill_root = Path(args.skill_root).resolve()
    cfg_path = Path(args.config).expanduser()
    cfg = load_config(cfg_path)

    if not args.skip_security and not args.dry_run:
        code = security_main(
            ["--config", str(cfg_path), "--skill-root", str(skill_root), "--mode", "digest"]
        )
        if code != 0:
            return code

    digest_cfg = cfg.get("digest") or {}
    to_email = (digest_cfg.get("to_email") or "").strip()
    if not to_email:
        raise SystemExit("CONFIG_INVALID: digest.to_email required")

    limit = int(args.limit or digest_cfg.get("daily_job_limit", 10))
    tz = ZoneInfo((cfg.get("schedule") or {}).get("timezone", "Asia/Shanghai"))
    now = datetime.now(tz)
    day = now.strftime("%Y-%m-%d")

    paths = cfg.get("paths") or {}
    state_path = resolve(paths.get("state"), skill_root) or Path.home() / ".job-outreach" / "state.json"
    cache_dir = resolve(paths.get("jobs_cache"), skill_root) or (Path.home() / ".job-outreach" / "cache")
    report_dir = resolve((cfg.get("report") or {}).get("dir"), skill_root) or (
        Path.home() / ".job-outreach" / "reports"
    )
    jobs_json = Path(args.jobs_json).expanduser() if args.jobs_json else (cache_dir / f"jobs-{day}.json")
    if not jobs_json.exists():
        raise SystemExit(f"JOBS_CACHE_MISSING: {jobs_json} （请先运行 collect_jobs.py）")

    payload = json.loads(jobs_json.read_text(encoding="utf-8"))
    selected = pick_jobs(payload, limit)
    if not selected:
        print("NO_JOBS: 今日无匹配岗位，跳过发送")
        return 0

    state = load_state(state_path)
    if state.get("digest_daily", {}).get(day) and not args.force and not args.dry_run:
        print(f"ALREADY_SENT: digest already sent for {day}")
        return 0

    subject_tpl = digest_cfg.get("subject", "【每日招聘速递】{date} · {count} 条新岗位")
    subject = subject_tpl.format(date=day, count=len(selected))
    from_name = ((cfg.get("email") or {}).get("from_name") or "求职助手").strip()
    user_note = (digest_cfg.get("user_note") or "").strip()
    text_body, html_body = render_digest(selected, day=day, user_note=user_note)

    result = send_text(
        cfg.get("mail") or {},
        to_email=to_email,
        subject=subject,
        body=text_body,
        from_name=from_name,
        html_body=html_body,
        dry_run=args.dry_run,
    )

    report_dir.mkdir(parents=True, exist_ok=True)
    template_path = skill_root / "assets" / "report_template.md"
    template = template_path.read_text(encoding="utf-8") if template_path.exists() else "# Report\n"
    rows = []
    for j in selected:
        rows.append(
            f"| {j.get('company_name','')} | {j.get('title','')} | {j.get('url','')} | {result.code} |"
        )
    report = (
        template.replace("{{date}}", day)
        .replace("{{slot}}", "digest")
        .replace("{{timezone}}", str(tz))
        .replace("{{dry_run}}", str(args.dry_run))
        .replace("{{generated_at}}", now.isoformat())
        .replace("{{success_count}}", "1" if result.ok else "0")
        .replace("{{fail_count}}", "0" if result.ok else "1")
        .replace("{{skip_count}}", "0")
        .replace("{{total_count}}", str(len(selected)))
        .replace(
            "{{result_rows}}",
            "\n".join(rows) if rows else "| (empty) | - | - | - |",
        )
    )
    # 兼容旧模板列数：若模板仍是 outreach 五列表头，额外写一份 digest 报告
    digest_report = (
        f"# 每日岗位摘要报告\n\n"
        f"- 日期：{day}\n"
        f"- 收件人：{to_email}\n"
        f"- 岗位数：{len(selected)}\n"
        f"- 发送结果：{result.code} / {result.message}\n"
        f"- Dry-run：{args.dry_run}\n\n"
        f"| 公司 | 岗位 | 链接 | 结果 |\n|------|------|------|------|\n"
        + ("\n".join(rows) if rows else "| - | - | - | - |")
        + "\n"
    )
    (report_dir / f"report-{day}-digest.md").write_text(digest_report, encoding="utf-8")
    (report_dir / f"report-{day}-digest-legacy.md").write_text(report, encoding="utf-8")

    if args.dry_run:
        print(f"DRY_RUN digest -> {to_email} jobs={len(selected)}")
        print(text_body[:500])
        return 0

    if not result.ok:
        print(f"FAIL {result.code}: {result.message}")
        return 1

    # 标记已见 + 今日已发
    for j in selected:
        jid = j.get("job_id")
        if jid:
            state["seen_jobs"][jid] = {
                "title": j.get("title"),
                "url": j.get("url"),
                "company_id": j.get("company_id"),
                "first_seen_at": now.isoformat(),
                "notified_at": now.isoformat(),
            }
    state["digest_daily"][day] = {
        "sent_at": now.isoformat(),
        "count": len(selected),
        "to": to_email,
    }
    save_state(state_path, state)
    print(f"OK digest -> {to_email} jobs={len(selected)} attempts={result.attempts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
