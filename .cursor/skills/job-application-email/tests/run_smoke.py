#!/usr/bin/env python3
"""无网络冒烟测试：校验安全检查与正文组装核心逻辑。"""

from __future__ import annotations

import json
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


def write_min_cfg(tmpdir: Path, resume: Path, companies: Path, intro: Path) -> Path:
    cfg = tmpdir / "config.yaml"
    cfg.write_text(
        f"""
mail:
  provider: smtp
  from_email: "sender@test.local"
  smtp_host: "smtp.test.local"
  smtp_port: 465
  smtp_ssl: true
  smtp_username: "sender@test.local"
  max_attachment_mb: 5
paths:
  companies: "{companies}"
  resume: "{resume}"
  self_intro: "{intro}"
  state: "{tmpdir / 'state.json'}"
schedule:
  batch_size: 3
security:
  daily_send_limit: 40
  blocked_domains: ["mailinator.com"]
report:
  dir: "{tmpdir / 'reports'}"
""",
        encoding="utf-8",
    )
    return cfg


def run_security(cfg: Path, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    import os

    env = os.environ.copy()
    env["JOB_OUTREACH_SMTP_PASSWORD"] = "dummy"
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "check_security.py"), "--config", str(cfg), "--json"],
        capture_output=True,
        text=True,
        env=env,
    )


def main() -> int:
    failures = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        resume = tmp / "resume.pdf"
        resume.write_bytes(b"%PDF-1.4 smoke")
        companies = tmp / "companies.csv"
        companies.write_text(
            "company_id,company_name,website,email,note\n"
            "c1,Good Co,https://good.example,hr@good.example,ok\n",
            encoding="utf-8",
        )
        intro = tmp / "self_intro.txt"
        intro.write_text(FIXED, encoding="utf-8")
        cfg = write_min_cfg(tmp, resume, companies, intro)

        # Pass case
        p = run_security(cfg)
        data = json.loads(p.stdout or "{}")
        if p.returncode != 0 or not data.get("ok"):
            failures.append(f"expected PASS, got rc={p.returncode} out={p.stdout} err={p.stderr}")

        # Intro mismatch
        intro.write_text(FIXED + "额外", encoding="utf-8")
        p = run_security(cfg)
        data = json.loads(p.stdout or "{}")
        codes = {f["code"] for f in data.get("findings", [])}
        if p.returncode == 0 or "INTRO_MISMATCH" not in codes:
            failures.append(f"INTRO_MISMATCH failed: {data}")
        intro.write_text(FIXED, encoding="utf-8")

        # Missing resume
        bad_cfg = write_min_cfg(tmp, tmp / "missing.pdf", companies, intro)
        p = run_security(bad_cfg)
        data = json.loads(p.stdout or "{}")
        codes = {f["code"] for f in data.get("findings", [])}
        if p.returncode == 0 or "RESUME_MISSING" not in codes:
            failures.append(f"RESUME_MISSING failed: {data}")

        # Blocked domain
        companies.write_text(
            "company_id,company_name,website,email,note\n"
            "c2,Bad,https://x,a@mailinator.com,x\n",
            encoding="utf-8",
        )
        p = run_security(cfg)
        data = json.loads(p.stdout or "{}")
        codes = {f["code"] for f in data.get("findings", [])}
        if p.returncode == 0 or "SECURITY_BLOCKED" not in codes:
            failures.append(f"SECURITY_BLOCKED failed: {data}")

    # Import body builder
    sys.path.insert(0, str(SCRIPTS))
    from send_batch import build_body

    with tempfile.TemporaryDirectory() as td:
        intro = Path(td) / "i.txt"
        intro.write_text(FIXED, encoding="utf-8")
        body = build_body({"email": {"closing": "谢谢"}}, intro)
        if not body.startswith(FIXED):
            failures.append("build_body intro mismatch")

    if failures:
        print("SMOKE FAIL")
        for f in failures:
            print("-", f)
        return 1
    print("SMOKE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
