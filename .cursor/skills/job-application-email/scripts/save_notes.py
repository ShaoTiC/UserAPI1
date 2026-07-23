#!/usr/bin/env python3
"""将全新岗位通过 DroiClaw MCP **notes_create_note** 写入手机便签。

手册：便签 / 待办（provider: notes）
创建笔记 notes_create_note —— 参数 title + content + folder_id
"""

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

from create_note import TOOL_NAME, notes_create_note


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
        return {"seen_jobs": {}, "push_log": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("seen_jobs", {})
    data.setdefault("push_log", [])
    return data


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, path.with_suffix(".json.bak"))
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def render_note_content(jobs: list[dict[str, Any]], *, when: str, user_note: str) -> str:
    lines = [
        f"采集时间：{when}",
        f"全新岗位数：{len(jobs)}",
        "",
    ]
    if user_note:
        lines.extend([user_note, ""])
    for i, job in enumerate(jobs, 1):
        title = job.get("title") or "(无标题)"
        company = job.get("company_name") or job.get("company_id") or ""
        website = job.get("website") or ""
        url = job.get("url") or ""
        snippet = job.get("snippet") or ""
        loc = job.get("location") or ""
        pub = job.get("published") or ""
        lines.append(f"{i}. {title}")
        lines.append(f"   公司：{company}")
        if website:
            lines.append(f"   官网：{website}")
        if loc or pub:
            lines.append(f"   信息：{' | '.join(x for x in [loc, pub] if x)}")
        lines.append(f"   职位链接：{url}")
        if snippet:
            lines.append(f"   职位内容：{snippet}")
        lines.append("")
    lines.append("（由 job-application-email skill · notes_create_note 生成）")
    return "\n".join(lines)


def render_single_job(job: dict[str, Any], *, when: str) -> str:
    return render_note_content([job], when=when, user_note="")


def pick_new_jobs(payload: dict[str, Any], limit: int | None) -> list[dict[str, Any]]:
    jobs = list(payload.get("new_jobs") or [])
    if limit is None or limit <= 0:
        return jobs
    return jobs[:limit]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="新岗位写入便签 create_note")
    parser.add_argument("--config", default=os.environ.get("JOB_OUTREACH_CONFIG"), required=False)
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--jobs-json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--skip-security", action="store_true")
    args = parser.parse_args(argv)

    if not args.config:
        raise SystemExit("请通过 --config 或 JOB_OUTREACH_CONFIG 指定配置")

    skill_root = Path(args.skill_root).resolve()
    cfg = load_config(Path(args.config).expanduser())

    notes_cfg = cfg.get("notes") or {}
    folder_id = str(notes_cfg.get("folder_id") or "job-digest").strip()
    one_per_job = bool(notes_cfg.get("one_note_per_job", False))
    notes_dir = notes_cfg.get("local_dir") or str(Path.home() / ".job-outreach" / "notes")

    digest_cfg = cfg.get("digest") or {}
    if args.limit is not None:
        limit = args.limit
    else:
        limit = int(digest_cfg.get("max_per_push", 30))

    tz = ZoneInfo((cfg.get("schedule") or {}).get("timezone", "Asia/Shanghai"))
    now = datetime.now(tz)
    when = now.strftime("%Y-%m-%d %H:%M")
    day = now.strftime("%Y-%m-%d")

    paths = cfg.get("paths") or {}
    state_path = resolve(paths.get("state"), skill_root) or Path.home() / ".job-outreach" / "state.json"
    cache_dir = resolve(paths.get("jobs_cache"), skill_root) or (Path.home() / ".job-outreach" / "cache")
    report_dir = resolve((cfg.get("report") or {}).get("dir"), skill_root) or (
        Path.home() / ".job-outreach" / "reports"
    )
    jobs_json = Path(args.jobs_json).expanduser() if args.jobs_json else (cache_dir / f"jobs-{day}.json")
    if not jobs_json.exists():
        raise SystemExit(f"JOBS_CACHE_MISSING: {jobs_json}")

    payload = json.loads(jobs_json.read_text(encoding="utf-8"))
    selected = pick_new_jobs(payload, limit if limit > 0 else None)
    if not selected:
        print("NO_NEW_JOBS: 无全新岗位，跳过创建笔记")
        return 0

    user_note = (digest_cfg.get("user_note") or "").strip()
    state = load_state(state_path)
    created: list[dict[str, Any]] = []

    if one_per_job:
        tasks = [
            (
                f"新岗位 · {j.get('company_name') or j.get('company_id')} · {j.get('title')}",
                render_single_job(j, when=when),
            )
            for j in selected
        ]
    else:
        title = f"新岗位速递 {when} · {len(selected)} 条"
        tasks = [(title, render_note_content(selected, when=when, user_note=user_note))]

    if args.dry_run:
        for title, content in tasks:
            print(f"DRY_RUN {TOOL_NAME} title={title!r} folder_id={folder_id!r}")
            print(content[:500])
            print("---")
        return 0

    for title, content in tasks:
        result = notes_create_note(title, content, folder_id, notes_dir=notes_dir)
        created.append(result.to_dict())
        print(
            f"OK {TOOL_NAME} provider={result.provider} path={result.path_or_uri} "
            f"msg={result.message}"
        )
        if not result.ok:
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
                "notify_channel": "notes_create_note",
            }
    state["push_log"].append(
        {
            "at": now.isoformat(),
            "count": len(selected),
            "channel": "notes",
            "tool": TOOL_NAME,
            "folder_id": folder_id,
            "notes": created,
        }
    )
    state["push_log"] = state["push_log"][-100:]
    save_state(state_path, state)

    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y%m%d-%H%M%S")
    report = (
        f"# 新岗位便签报告\n\n"
        f"- 时间：{when}\n"
        f"- 渠道：notes / {TOOL_NAME}\n"
        f"- folder_id：{folder_id}\n"
        f"- 岗位数：{len(selected)}\n"
        f"- 笔记数：{len(created)}\n\n"
        f"```json\n{json.dumps(created, ensure_ascii=False, indent=2)}\n```\n"
    )
    (report_dir / f"report-{stamp}-notes.md").write_text(report, encoding="utf-8")
    print(f"OK {TOOL_NAME} saved jobs={len(selected)} notes={len(created)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
