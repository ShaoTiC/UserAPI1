#!/usr/bin/env python3
"""发送前安全与合规检查。退出码 0 = 通过；非 0 = 阻断发送。"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
FIXED_INTRO = (
    "我是东北农业大学计算机专业大四的本科生,Java基础扎实且掌握Agent开发,"
    "有后端实习经历,独立开发智能体协作平台。"
)

# 明显不可投 / 高风险域名（可在 config.security.blocked_domains 扩展）
DEFAULT_BLOCKED_DOMAINS = {
    "example.com",
    "example.org",
    "mailinator.com",
    "guerrillamail.com",
    "10minutemail.com",
}


class Finding:
    def __init__(self, level: str, code: str, message: str) -> None:
        self.level = level  # ERROR / WARN / INFO
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"[{self.level}] {self.code}: {self.message}"


def load_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"CONFIG_INVALID: config not found: {path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML not installed. Run: pip install pyyaml")
        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("CONFIG_INVALID: root must be a mapping")
    return data


def resolve_path(raw: str | None, base: Path | None = None) -> Path | None:
    if not raw:
        return None
    p = Path(os.path.expanduser(raw))
    if not p.is_absolute() and base is not None:
        p = (base / p).resolve()
    return p


def check_intro(intro_path: Path | None, findings: list[Finding]) -> None:
    if intro_path is None or not intro_path.exists():
        findings.append(
            Finding("WARN", "INTRO_FILE_MISSING", "未找到 self_intro.txt，将使用内置固定文案校验")
        )
        actual = FIXED_INTRO
    else:
        actual = intro_path.read_text(encoding="utf-8").strip()
    if actual != FIXED_INTRO:
        findings.append(
            Finding(
                "ERROR",
                "INTRO_MISMATCH",
                "自我介绍与固定原文不一致，禁止发送。请恢复 assets/self_intro.txt",
            )
        )
    else:
        findings.append(Finding("INFO", "INTRO_OK", "自我介绍与固定原文一致"))


def check_resume(resume_path: Path | None, max_mb: float, findings: list[Finding]) -> None:
    if resume_path is None or not resume_path.exists():
        findings.append(Finding("ERROR", "RESUME_MISSING", f"简历不存在: {resume_path}"))
        return
    if resume_path.suffix.lower() != ".pdf":
        findings.append(Finding("ERROR", "RESUME_TYPE", "简历必须是 PDF"))
        return
    size_mb = resume_path.stat().st_size / (1024 * 1024)
    if size_mb <= 0:
        findings.append(Finding("ERROR", "RESUME_EMPTY", "简历文件为空"))
    elif size_mb > max_mb:
        findings.append(
            Finding(
                "ERROR",
                "ATTACHMENT_TOO_LARGE",
                f"简历 {size_mb:.2f}MB 超过上限 {max_mb}MB",
            )
        )
    else:
        findings.append(Finding("INFO", "RESUME_OK", f"简历通过: {resume_path} ({size_mb:.2f}MB)"))


def check_companies_outreach(companies_path: Path | None, blocked: set[str], findings: list[Finding]) -> int:
    if companies_path is None or not companies_path.exists():
        findings.append(Finding("ERROR", "COMPANIES_MISSING", f"公司列表不存在: {companies_path}"))
        return 0
    valid = 0
    with companies_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"company_id", "company_name", "email"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            findings.append(
                Finding(
                    "ERROR",
                    "COMPANIES_SCHEMA",
                    f"CSV 必须包含列: {sorted(required)}；实际: {reader.fieldnames}",
                )
            )
            return 0
        for i, row in enumerate(reader, start=2):
            email = (row.get("email") or "").strip()
            cid = (row.get("company_id") or "").strip()
            if not cid:
                findings.append(Finding("ERROR", "COMPANY_ID_MISSING", f"L{i}: company_id 为空"))
                continue
            if not EMAIL_RE.match(email):
                findings.append(
                    Finding("ERROR", "INVALID_EMAIL", f"L{i} ({cid}): 非法邮箱 '{email}'")
                )
                continue
            domain = email.split("@", 1)[1].lower()
            if domain in blocked:
                findings.append(
                    Finding(
                        "ERROR",
                        "SECURITY_BLOCKED",
                        f"L{i} ({cid}): 域名被拦截 {domain}",
                    )
                )
                continue
            valid += 1
    if valid == 0:
        findings.append(Finding("ERROR", "NO_VALID_RECIPIENTS", "没有可发送的有效收件人"))
    else:
        findings.append(Finding("INFO", "COMPANIES_OK", f"有效收件人 {valid} 条"))
    return valid


def check_companies_digest(companies_path: Path | None, findings: list[Finding]) -> int:
    if companies_path is None or not companies_path.exists():
        findings.append(Finding("ERROR", "COMPANIES_MISSING", f"公司列表不存在: {companies_path}"))
        return 0
    valid = 0
    with companies_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"company_id", "company_name", "careers_url", "source_type"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            findings.append(
                Finding(
                    "ERROR",
                    "COMPANIES_SCHEMA",
                    f"digest 模式 CSV 必须包含列: {sorted(required)}；实际: {reader.fieldnames}",
                )
            )
            return 0
        allowed = {"rss", "html_regex", "json", "fixture"}
        for i, row in enumerate(reader, start=2):
            cid = (row.get("company_id") or "").strip()
            careers = (row.get("careers_url") or "").strip()
            st = (row.get("source_type") or "").strip().lower()
            if not cid:
                findings.append(Finding("ERROR", "COMPANY_ID_MISSING", f"L{i}: company_id 为空"))
                continue
            if not careers:
                findings.append(Finding("ERROR", "CAREERS_URL_MISSING", f"L{i} ({cid}): careers_url 为空"))
                continue
            if st not in allowed:
                findings.append(
                    Finding(
                        "ERROR",
                        "SOURCE_TYPE_INVALID",
                        f"L{i} ({cid}): source_type 须为 {sorted(allowed)}",
                    )
                )
                continue
            if st == "html_regex" and not (row.get("item_regex") or "").strip():
                findings.append(
                    Finding("ERROR", "ITEM_REGEX_MISSING", f"L{i} ({cid}): html_regex 需要 item_regex")
                )
                continue
            valid += 1
    if valid == 0:
        findings.append(Finding("ERROR", "NO_VALID_SOURCES", "没有可采集的有效公司源"))
    else:
        findings.append(Finding("INFO", "COMPANIES_OK", f"有效采集源 {valid} 条"))
    return valid


def check_digest_config(cfg: dict, findings: list[Finding]) -> None:
    digest = cfg.get("digest") or {}
    to_email = (digest.get("to_email") or "").strip()
    if not EMAIL_RE.match(to_email):
        findings.append(Finding("ERROR", "CONFIG_INVALID", "digest.to_email 非法或缺失"))
    limit = int(digest.get("daily_job_limit", 10))
    if limit <= 0 or limit > 50:
        findings.append(
            Finding("ERROR", "CONFIG_INVALID", "digest.daily_job_limit 应在 1–50（建议约 10）")
        )
    else:
        findings.append(Finding("INFO", "DIGEST_OK", f"摘要将发送到 {to_email}，每日约 {limit} 条"))


def check_mail_config(cfg: dict, findings: list[Finding], mode: str = "digest") -> None:
    mail = cfg.get("mail") or {}
    provider = (mail.get("provider") or "smtp").lower()
    sender = (mail.get("from_email") or "").strip()
    if not EMAIL_RE.match(sender):
        findings.append(Finding("ERROR", "CONFIG_INVALID", "mail.from_email 非法或缺失"))
    if provider == "smtp":
        for key in ("smtp_host", "smtp_port", "smtp_username"):
            if not mail.get(key):
                findings.append(Finding("ERROR", "CONFIG_INVALID", f"mail.{key} 缺失"))
        pwd = os.environ.get("JOB_OUTREACH_SMTP_PASSWORD") or mail.get("smtp_password")
        if not pwd:
            findings.append(
                Finding(
                    "ERROR",
                    "AUTH_MISSING",
                    "缺少 SMTP 密码：设置环境变量 JOB_OUTREACH_SMTP_PASSWORD",
                )
            )
        if mail.get("smtp_password"):
            findings.append(
                Finding(
                    "WARN",
                    "SECRET_IN_FILE",
                    "config 中明文写了 smtp_password，建议改为环境变量",
                )
            )
    elif provider == "http_api":
        if not mail.get("api_url"):
            findings.append(Finding("ERROR", "CONFIG_INVALID", "mail.api_url 缺失"))
        key = os.environ.get("JOB_OUTREACH_API_KEY") or mail.get("api_key")
        if not key:
            findings.append(
                Finding(
                    "ERROR",
                    "AUTH_MISSING",
                    "缺少 API Key：设置环境变量 JOB_OUTREACH_API_KEY",
                )
            )
    else:
        findings.append(Finding("ERROR", "CONFIG_INVALID", f"未知 mail.provider: {provider}"))

    if mode == "outreach":
        batch = (cfg.get("schedule") or {}).get("batch_size", 5)
        daily_cap = (cfg.get("security") or {}).get("daily_send_limit", 40)
        if int(batch) > int(daily_cap):
            findings.append(
                Finding(
                    "ERROR",
                    "SECURITY_BLOCKED",
                    f"batch_size({batch}) 大于 daily_send_limit({daily_cap})",
                )
            )


def check_state(state_path: Path | None, findings: list[Finding]) -> None:
    if state_path is None or not state_path.exists():
        findings.append(Finding("INFO", "STATE_NEW", "状态文件不存在，将在首次发送时创建"))
        return
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("root not object")
        findings.append(Finding("INFO", "STATE_OK", f"状态文件可读: {state_path}"))
    except Exception as exc:  # noqa: BLE001
        findings.append(Finding("ERROR", "STATE_CORRUPT", f"state.json 损坏: {exc}"))


def run_checks(
    cfg: dict,
    skill_root: Path,
    companies_override: Path | None,
    resume_override: Path | None,
    mode: str = "digest",
) -> list[Finding]:
    findings: list[Finding] = []
    assets = skill_root / "assets"
    companies = companies_override or resolve_path((cfg.get("paths") or {}).get("companies"), skill_root)
    resume = resume_override or resolve_path((cfg.get("paths") or {}).get("resume"), skill_root)
    intro = resolve_path((cfg.get("paths") or {}).get("self_intro"), skill_root) or (assets / "self_intro.txt")
    state = resolve_path((cfg.get("paths") or {}).get("state"), skill_root)

    max_mb = float((cfg.get("mail") or {}).get("max_attachment_mb", 5))
    blocked = set(DEFAULT_BLOCKED_DOMAINS)
    blocked.update({d.lower() for d in ((cfg.get("security") or {}).get("blocked_domains") or [])})

    check_mail_config(cfg, findings, mode=mode)
    check_state(state, findings)

    if mode == "digest":
        check_digest_config(cfg, findings)
        check_companies_digest(companies, findings)
    else:
        check_intro(intro, findings)
        check_resume(resume, max_mb, findings)
        check_companies_outreach(companies, blocked, findings)
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="求职 skill 安全检查")
    parser.add_argument("--config", required=True, help="config.yaml 路径")
    parser.add_argument("--companies", help="覆盖 config 中的公司列表路径")
    parser.add_argument("--resume", help="覆盖 config 中的简历路径")
    parser.add_argument(
        "--mode",
        choices=["digest", "outreach"],
        default="digest",
        help="digest=岗位摘要（默认）；outreach=向外投递简历",
    )
    parser.add_argument(
        "--skill-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="skill 根目录",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = parser.parse_args(argv)

    findings: list[Finding]
    try:
        cfg = load_config(Path(args.config).expanduser())
        argv_list = list(argv) if argv is not None else sys.argv[1:]
        if any(a == "--mode" or a.startswith("--mode=") for a in argv_list):
            mode = args.mode
        else:
            mode = (cfg.get("mode") or "digest").lower()
            if mode not in {"digest", "outreach"}:
                mode = "digest"
        findings = run_checks(
            cfg,
            Path(args.skill_root).resolve(),
            Path(args.companies).expanduser() if args.companies else None,
            Path(args.resume).expanduser() if args.resume else None,
            mode=mode,
        )
    except Exception as exc:  # noqa: BLE001
        findings = [Finding("ERROR", "CONFIG_INVALID", str(exc))]

    errors = [f for f in findings if f.level == "ERROR"]
    if args.json:
        payload = {
            "ok": not errors,
            "findings": [f.__dict__ for f in findings],
            "error_count": len(errors),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for f in findings:
            print(f)
        print("---")
        print("PASS" if not errors else f"FAIL ({len(errors)} errors)")

    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
