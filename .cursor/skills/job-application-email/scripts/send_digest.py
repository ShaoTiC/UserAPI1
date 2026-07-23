#!/usr/bin/env python3
"""将「全新」岗位立刻推送到用户邮箱（只发新岗位，宁少勿多）。"""

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


def render_digest(jobs: list[dict[str, Any]], *, when: str, user_note: str) -> tuple[str, str]:
    lines = [
        f"【新岗位速递】{when}",
        "",
        f"检测到 {len(jobs)} 条全新匹配岗位（仅推送新发布/未见过的岗位）。",
        "",
    ]
    if user_note:
        lines.extend([user_note, ""])
    html = [
        f"<h2>【新岗位速递】{when}</h2>",
        f"<p>检测到 <b>{len(jobs)}</b> 条全新匹配岗位（只发全新，宁少勿多）。</p>",
    ]
    if user_note:
        html.append(f"<p>{user_note}</p>")
    html.append("<ol>")
    for i, job in enumerate(jobs, 1):
        title = job.get("title") or "(无标题)"
        company = job.get("company_name") or job.get("company_id") or ""
        website = job.get("website") or ""
        url = job.get("url") or ""
        loc = job.get("location") or ""
        pub = job.get("published") or ""
        snippet = job.get("snippet") or ""
        lines.append(f"{i}. {title}")
        lines.append(f"   公司: {company}")
        if website:
            lines.append(f"   官网: {website}")
        if loc or pub:
            lines.append(f"   信息: {' | '.join(x for x in [loc, pub] if x)}")
        lines.append(f"   职位链接: {url}")
        if snippet:
            lines.append(f"   职位内容: {snippet}")
        lines.append("")
        html.append("<li>")
        html.append(f"<p><b>{title}</b><br/>公司：{company}</p>")
        if website:
            html.append(f'<p>官网：<a href="{website}">{website}</a></p>')
        if loc or pub:
            html.append(f"<p>{' | '.join(x for x in [loc, pub] if x)}</p>")
        html.append(f'<p>职位链接：<a href="{url}">{url}</a></p>')
        if snippet:
            html.append(f"<p>职位内容：{snippet}</p>")
        html.append("</li>")
    html.append("</ol>")
    html.append("<p style='color:#666'>本邮件由 job-application-email skill 在发现更新后立即发送。</p>")
    lines.append("— 发现官网更新后立即推送（job-application-email skill）")
    return "\n".join(lines), "\n".join(html)


def pick_jobs(payload: dict[str, Any], limit: int | None) -> list[dict[str, Any]]:
    """只取全新岗位；不补齐已知岗位。"""
    new_jobs = list(payload.get("new_jobs") or [])
    if limit is None or limit <= 0:
        return new_jobs
    return new_jobs[:limit]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="发送新岗位速递到用户邮箱")
    parser.add_argument("--config", default=os.environ.get("JOB_OUTREACH_CONFIG"), required=False)
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--jobs-json", help="collect_jobs 输出的 JSON；默认读当日 cache")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="单次推送上限（默认 digest.max_per_push；0/不设表示不截断）",
    )
    parser.add_argument("--skip-security", action="store_true")
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

    # 只发全新；上限仅防止单次邮件过大，不是「必须凑满」
    if args.limit is not None:
        limit = args.limit
    else:
        limit = int(digest_cfg.get("max_per_push", 30))

    tz = ZoneInfo((cfg.get("schedule") or {}).get("timezone", "Asia/Shanghai"))
    now = datetime.now(tz)
    day = now.strftime("%Y-%m-%d")
    when = now.strftime("%Y-%m-%d %H:%M")

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
    selected = pick_jobs(payload, limit if limit > 0 else None)
    if not selected:
        print("NO_NEW_JOBS: 无全新岗位，跳过发送")
        return 0

    state = load_state(state_path)
    subject_tpl = digest_cfg.get("subject", "【新岗位速递】{datetime} · {count} 条更新")
    subject = subject_tpl.format(date=day, datetime=when, count=len(selected))
    from_name = ((cfg.get("email") or {}).get("from_name") or "求职助手").strip()
    user_note = (digest_cfg.get("user_note") or "").strip()
    text_body, html_body = render_digest(selected, when=when, user_note=user_note)

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
    rows = []
    for j in selected:
        rows.append(
            f"| {j.get('company_name','')} | {j.get('title','')} | {j.get('url','')} | {result.code} |"
        )
    stamp = now.strftime("%Y%m%d-%H%M%S")
    digest_report = (
        f"# 新岗位速递报告\n\n"
        f"- 时间：{when}\n"
        f"- 收件人：{to_email}\n"
        f"- 新岗位数：{len(selected)}\n"
        f"- 发送结果：{result.code} / {result.message}\n"
        f"- Dry-run：{args.dry_run}\n\n"
        f"| 公司 | 岗位 | 链接 | 结果 |\n|------|------|------|------|\n"
        + ("\n".join(rows) if rows else "| - | - | - | - |")
        + "\n"
    )
    (report_dir / f"report-{stamp}-digest.md").write_text(digest_report, encoding="utf-8")

    if args.dry_run:
        print(f"DRY_RUN digest -> {to_email} new_jobs={len(selected)}")
        print(text_body[:800])
        return 0

    if not result.ok:
        print(f"FAIL {result.code}: {result.message}")
        return 1

    for j in selected:
        jid = j.get("job_id")
        if jid:
            state["seen_jobs"][jid] = {
                "title": j.get("title"),
                "url": j.get("url"),
                "company_id": j.get("company_id"),
                "website": j.get("website"),
                "first_seen_at": now.isoformat(),
                "notified_at": now.isoformat(),
            }
    state.setdefault("push_log", []).append(
        {"at": now.isoformat(), "count": len(selected), "to": to_email}
    )
    # 只保留最近 100 条推送日志
    state["push_log"] = state["push_log"][-100:]
    save_state(state_path, state)
    print(f"OK digest -> {to_email} new_jobs={len(selected)} attempts={result.attempts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
