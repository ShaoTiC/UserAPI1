#!/usr/bin/env python3
"""无网络冒烟：digest 采集/安全检查 + outreach 兼容要点。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXED = (
    "我是东北农业大学计算机专业大四的本科生,Java基础扎实且掌握Agent开发,"
    "有后端实习经历,独立开发智能体协作平台。"
)


def run(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess:
    base = os.environ.copy()
    base["JOB_OUTREACH_SMTP_PASSWORD"] = "dummy"
    if env:
        base.update(env)
    return subprocess.run(cmd, capture_output=True, text=True, env=base)


def main() -> int:
    failures: list[str] = []
    sys.path.insert(0, str(SCRIPTS))

    # --- digest: fixture collect ---
    from job_sources import collect_from_row, match_keywords
    from send_digest import pick_jobs

    payload = {
        "new_jobs": [{"job_id": "1", "title": "Java实习"}],
        "known_jobs": [{"job_id": "2", "title": "Java正式"}],
    }
    selected = pick_jobs(payload, 10)
    if len(selected) != 1 or selected[0]["job_id"] != "1":
        failures.append(f"pick_jobs should only use new_jobs, got {selected}")

    row = {
        "company_id": "demo001",
        "company_name": "示例科技A",
        "careers_url": "assets/fixtures/demo_jobs_a.json",
        "source_type": "fixture",
        "keywords": "Java|后端|实习|Agent",
    }
    jobs, err = collect_from_row(row, skill_root=ROOT, global_keywords=[])
    if err:
        failures.append(f"fixture collect error: {err}")
    titles = {j.title for j in jobs}
    if "Java后端开发实习生" not in titles or "Agent 平台研发实习生" not in titles:
        failures.append(f"expected matched titles, got {titles}")
    if any("前端" in t for t in titles):
        failures.append("frontend job should be filtered")

    if match_keywords("产品运营助理", ["Java", "后端"]):
        failures.append("keyword match should fail for 运营")

    # --- digest security ---
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        companies = tmp / "companies.csv"
        companies.write_text(
            "company_id,company_name,website,careers_url,source_type,item_regex,keywords,email,note\n"
            f"demo001,A,,{(ROOT / 'assets/fixtures/demo_jobs_a.json').as_posix()},fixture,,,Java,,\n",
            encoding="utf-8",
        )
        cfg = tmp / "config.yaml"
        cfg.write_text(
            f"""
mode: digest
mail:
  provider: smtp
  from_email: "3461630168@qq.com"
  smtp_host: "smtp.qq.com"
  smtp_port: 465
  smtp_ssl: true
  smtp_username: "3461630168@qq.com"
digest:
  to_email: "3461630168@qq.com"
  max_per_push: 30
  keywords: ["Java", "后端"]
paths:
  companies: "{companies.as_posix()}"
  state: "{(tmp / 'state.json').as_posix()}"
  jobs_cache: "{(tmp / 'cache').as_posix()}"
schedule:
  timezone: "Asia/Shanghai"
  poll_interval_sec: 600
crawl:
  baseline_on_first_run: false
report:
  dir: "{(tmp / 'reports').as_posix()}"
""",
            encoding="utf-8",
        )
        p = run(
            [
                sys.executable,
                str(SCRIPTS / "check_security.py"),
                "--config",
                str(cfg),
                "--mode",
                "digest",
                "--json",
            ]
        )
        data = json.loads(p.stdout or "{}")
        if p.returncode != 0 or not data.get("ok"):
            failures.append(f"digest security expected PASS: {p.stdout} {p.stderr}")

        # collect + dry-run digest
        p = run(
            [sys.executable, str(SCRIPTS / "collect_jobs.py"), "--config", str(cfg), "--skill-root", str(ROOT)]
        )
        if p.returncode != 0:
            failures.append(f"collect_jobs failed: {p.stdout}\n{p.stderr}")
        p = run(
            [
                sys.executable,
                str(SCRIPTS / "send_digest.py"),
                "--config",
                str(cfg),
                "--skill-root",
                str(ROOT),
                "--dry-run",
                "--limit",
                "10",
                "--skip-security",
            ]
        )
        if p.returncode != 0 or "DRY_RUN" not in (p.stdout + p.stderr):
            failures.append(f"send_digest dry-run failed: {p.stdout}\n{p.stderr}")

        # digest should not require resume
        codes = {f["code"] for f in data.get("findings", [])}
        if "RESUME_MISSING" in codes:
            failures.append("digest mode should not require resume")

    # --- outreach intro still enforced when mode=outreach ---
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        resume = tmp / "r.pdf"
        resume.write_bytes(b"%PDF-1.4 x")
        companies = tmp / "c.csv"
        companies.write_text(
            "company_id,company_name,website,email,note\nc1,Co,https://x,hr@good.example,x\n",
            encoding="utf-8",
        )
        intro = tmp / "i.txt"
        intro.write_text(FIXED, encoding="utf-8")
        cfg = tmp / "cfg.yaml"
        cfg.write_text(
            f"""
mode: outreach
mail:
  provider: smtp
  from_email: "a@test.local"
  smtp_host: "smtp.test.local"
  smtp_port: 465
  smtp_username: "a@test.local"
  max_attachment_mb: 5
paths:
  companies: "{companies.as_posix()}"
  resume: "{resume.as_posix()}"
  self_intro: "{intro.as_posix()}"
  state: "{(tmp / 's.json').as_posix()}"
schedule:
  batch_size: 3
security:
  daily_send_limit: 40
""",
            encoding="utf-8",
        )
        p = run(
            [
                sys.executable,
                str(SCRIPTS / "check_security.py"),
                "--config",
                str(cfg),
                "--mode",
                "outreach",
                "--json",
            ]
        )
        data = json.loads(p.stdout or "{}")
        if p.returncode != 0 or not data.get("ok"):
            failures.append(f"outreach security expected PASS: {data}")

        intro.write_text(FIXED + "x", encoding="utf-8")
        p = run(
            [
                sys.executable,
                str(SCRIPTS / "check_security.py"),
                "--config",
                str(cfg),
                "--mode",
                "outreach",
                "--json",
            ]
        )
        data = json.loads(p.stdout or "{}")
        codes = {f["code"] for f in data.get("findings", [])}
        if p.returncode == 0 or "INTRO_MISMATCH" not in codes:
            failures.append(f"outreach INTRO_MISMATCH failed: {data}")

    if failures:
        print("SMOKE FAIL")
        for f in failures:
            print("-", f)
        return 1
    print("SMOKE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
