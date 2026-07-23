#!/usr/bin/env python3
"""采集目标公司新岗位，写入当日缓存并打印摘要。"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from job_sources import JobPosting, collect_from_row


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


def load_seen(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return {"seen_jobs": {}, "digest_daily": {}, "records": {}, "daily": {}}
    data = json.loads(state_path.read_text(encoding="utf-8"))
    data.setdefault("seen_jobs", {})
    data.setdefault("digest_daily", {})
    data.setdefault("records", {})
    data.setdefault("daily", {})
    return data


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="采集公司招聘岗位")
    parser.add_argument("--config", default=os.environ.get("JOB_OUTREACH_CONFIG"), required=False)
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--out", help="输出 JSON 路径（默认 cache/jobs-YYYY-MM-DD.json）")
    parser.add_argument("--limit-per-company", type=int, default=None)
    args = parser.parse_args(argv)

    if not args.config:
        raise SystemExit("请通过 --config 或 JOB_OUTREACH_CONFIG 指定配置")

    skill_root = Path(args.skill_root).resolve()
    cfg = load_config(Path(args.config).expanduser())
    paths = cfg.get("paths") or {}
    companies_path = resolve(paths.get("companies"), skill_root)
    state_path = resolve(paths.get("state"), skill_root) or Path.home() / ".job-outreach" / "state.json"
    cache_dir = resolve(paths.get("jobs_cache"), skill_root) or (Path.home() / ".job-outreach" / "cache")

    if companies_path is None or not companies_path.exists():
        raise SystemExit(f"COMPANIES_MISSING: {companies_path}")

    tz = ZoneInfo((cfg.get("schedule") or {}).get("timezone", "Asia/Shanghai"))
    day = datetime.now(tz).strftime("%Y-%m-%d")
    digest_cfg = cfg.get("digest") or {}
    global_keywords = list(digest_cfg.get("keywords") or [])
    timeout = float((cfg.get("crawl") or {}).get("timeout_sec", 25))
    wait_ms = int((cfg.get("crawl") or {}).get("playwright_wait_ms", 6000))
    per_company = int(
        args.limit_per_company
        if args.limit_per_company is not None
        else (cfg.get("crawl") or {}).get("limit_per_company", 40)
    )
    seed_baseline = bool((cfg.get("crawl") or {}).get("baseline_on_first_run", True))

    with companies_path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    state = load_seen(state_path)
    seen = state["seen_jobs"]
    first_run = seed_baseline and len(seen) == 0
    all_jobs: list[JobPosting] = []
    errors: list[dict[str, str]] = []

    for row in rows:
        cid = (row.get("company_id") or "").strip()
        if not cid:
            continue
        jobs, err = collect_from_row(
            row,
            skill_root=skill_root,
            timeout=timeout,
            global_keywords=global_keywords,
            playwright_wait_ms=wait_ms,
        )
        if err:
            errors.append({"company_id": cid, "error": err})
            print(f"WARN {cid}: {err}")
            continue
        jobs = jobs[:per_company]
        print(f"OK {cid}: fetched {len(jobs)} matched jobs")
        all_jobs.extend(jobs)

    # 去重：全局未见过的优先
    new_jobs: list[JobPosting] = []
    known_jobs: list[JobPosting] = []
    dedup: set[str] = set()
    for job in all_jobs:
        if job.job_id in dedup:
            continue
        dedup.add(job.job_id)
        if job.job_id in seen:
            known_jobs.append(job)
        else:
            new_jobs.append(job)

    if first_run and new_jobs:
        # 首次运行：建立基线，不作为「新岗位」推送，避免把存量岗位一次性刷屏
        now_iso = datetime.now(tz).isoformat()
        for job in new_jobs:
            state["seen_jobs"][job.job_id] = {
                "title": job.title,
                "url": job.url,
                "company_id": job.company_id,
                "first_seen_at": now_iso,
                "baseline": True,
            }
        save_json(state_path, state)
        print(f"BASELINE: seeded {len(new_jobs)} jobs without notify")
        known_jobs = new_jobs + known_jobs
        new_jobs = []

    out_path = Path(args.out).expanduser() if args.out else (cache_dir / f"jobs-{day}.json")
    payload = {
        "date": day,
        "new_count": len(new_jobs),
        "known_count": len(known_jobs),
        "error_count": len(errors),
        "errors": errors,
        "new_jobs": [j.to_dict() for j in new_jobs],
        "known_jobs": [j.to_dict() for j in known_jobs],
    }
    save_json(out_path, payload)
    print(f"Wrote {out_path} new={len(new_jobs)} known={len(known_jobs)} errors={len(errors)}")
    return 0 if not (len(new_jobs) == 0 and errors and not known_jobs) else 1


if __name__ == "__main__":
    sys.exit(main())
