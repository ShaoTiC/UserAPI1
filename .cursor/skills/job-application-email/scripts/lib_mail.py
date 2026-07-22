#!/usr/bin/env python3
"""邮件发送底层：SMTP 与通用 HTTP API，含指数退避重试。"""

from __future__ import annotations

import json
import os
import smtplib
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Callable


@dataclass
class SendResult:
    ok: bool
    code: str
    message: str
    attempts: int = 1


class PermanentSendError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class TransientSendError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _sleep_backoff(attempt: int, base: float) -> None:
    time.sleep(base * (2 ** (attempt - 1)))


def with_retries(
    fn: Callable[[], None],
    *,
    max_retries: int,
    base_delay: float,
    on_auth_fail_abort: bool = True,
) -> SendResult:
    attempts = 0
    last_exc: Exception | None = None
    while attempts < max_retries:
        attempts += 1
        try:
            fn()
            return SendResult(True, "OK", "sent", attempts=attempts)
        except PermanentSendError as exc:
            return SendResult(False, exc.code, exc.message, attempts=attempts)
        except TransientSendError as exc:
            last_exc = exc
            if exc.code == "AUTH_FAILED" and on_auth_fail_abort:
                return SendResult(False, exc.code, exc.message, attempts=attempts)
            if attempts >= max_retries:
                break
            _sleep_backoff(attempts, base_delay)
        except Exception as exc:  # noqa: BLE001
            last_exc = TransientSendError("TIMEOUT", str(exc))
            if attempts >= max_retries:
                break
            _sleep_backoff(attempts, base_delay)
    assert last_exc is not None
    code = getattr(last_exc, "code", "TIMEOUT")
    message = getattr(last_exc, "message", str(last_exc))
    return SendResult(False, code, message, attempts=attempts)


def build_message(
    *,
    from_email: str,
    from_name: str,
    to_email: str,
    subject: str,
    body: str,
    resume_path: Path,
    attach_name: str | None = None,
) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    data = resume_path.read_bytes()
    filename = attach_name or resume_path.name
    msg.add_attachment(data, maintype="application", subtype="pdf", filename=filename)
    return msg


def send_smtp(mail_cfg: dict[str, Any], msg: EmailMessage) -> None:
    host = mail_cfg["smtp_host"]
    port = int(mail_cfg.get("smtp_port", 465))
    username = mail_cfg["smtp_username"]
    password = os.environ.get("JOB_OUTREACH_SMTP_PASSWORD") or mail_cfg.get("smtp_password")
    if not password:
        raise PermanentSendError("AUTH_MISSING", "JOB_OUTREACH_SMTP_PASSWORD not set")
    use_ssl = bool(mail_cfg.get("smtp_ssl", port == 465))
    timeout = float(mail_cfg.get("timeout_sec", 30))
    try:
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, timeout=timeout, context=context) as server:
                server.login(username, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=timeout) as server:
                server.ehlo()
                if mail_cfg.get("smtp_starttls", True):
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                server.login(username, password)
                server.send_message(msg)
    except smtplib.SMTPAuthenticationError as exc:
        raise TransientSendError("AUTH_FAILED", str(exc)) from exc
    except smtplib.SMTPRecipientsRefused as exc:
        raise PermanentSendError("INVALID_RECIPIENT", str(exc)) from exc
    except smtplib.SMTPDataError as exc:
        # 552/554 等常与附件/垃圾相关
        err = str(exc)
        if "spam" in err.lower() or getattr(exc, "smtp_code", 0) in {550, 554}:
            raise PermanentSendError("SPAM_REJECTED", err) from exc
        raise TransientSendError("RATE_LIMITED", err) from exc
    except (TimeoutError, smtplib.SMTPServerDisconnected, ConnectionError, OSError) as exc:
        raise TransientSendError("TIMEOUT", str(exc)) from exc


def send_http_api(mail_cfg: dict[str, Any], payload: dict[str, Any]) -> None:
    api_url = mail_cfg["api_url"]
    api_key = os.environ.get("JOB_OUTREACH_API_KEY") or mail_cfg.get("api_key")
    if not api_key:
        raise PermanentSendError("AUTH_MISSING", "JOB_OUTREACH_API_KEY not set")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "job-application-email-skill/1.0",
    }
    # 允许自定义 header 名
    if mail_cfg.get("api_key_header"):
        headers.pop("Authorization", None)
        headers[mail_cfg["api_key_header"]] = api_key
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, headers=headers, method="POST")
    timeout = float(mail_cfg.get("timeout_sec", 30))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status >= 400:
                body = resp.read().decode("utf-8", errors="replace")
                raise TransientSendError("HTTP_ERROR", f"{resp.status}: {body}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code in {401, 403}:
            raise TransientSendError("AUTH_FAILED", f"{exc.code}: {body}") from exc
        if exc.code == 429:
            raise TransientSendError("RATE_LIMITED", body) from exc
        if exc.code in {400, 422}:
            raise PermanentSendError("INVALID_RECIPIENT", body) from exc
        raise TransientSendError("HTTP_ERROR", f"{exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise TransientSendError("TIMEOUT", str(exc)) from exc


def send_one(
    mail_cfg: dict[str, Any],
    *,
    to_email: str,
    subject: str,
    body: str,
    resume_path: Path,
    from_name: str,
    attach_name: str | None = None,
    dry_run: bool = False,
) -> SendResult:
    max_retries = int(mail_cfg.get("max_retries", 3))
    base_delay = float(mail_cfg.get("retry_base_delay_sec", 2))
    from_email = mail_cfg["from_email"]

    if dry_run:
        return SendResult(True, "DRY_RUN", f"preview -> {to_email}", attempts=0)

    provider = (mail_cfg.get("provider") or "smtp").lower()

    def _do() -> None:
        if provider == "smtp":
            msg = build_message(
                from_email=from_email,
                from_name=from_name,
                to_email=to_email,
                subject=subject,
                body=body,
                resume_path=resume_path,
                attach_name=attach_name,
            )
            send_smtp(mail_cfg, msg)
        elif provider == "http_api":
            # 通用 JSON；具体字段名可用 mail.api_payload_map 微调
            import base64

            payload = {
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "text": body,
                "attachments": [
                    {
                        "filename": attach_name or resume_path.name,
                        "content": base64.b64encode(resume_path.read_bytes()).decode("ascii"),
                    }
                ],
            }
            payload.update(mail_cfg.get("api_extra_fields") or {})
            send_http_api(mail_cfg, payload)
        else:
            raise PermanentSendError("CONFIG_INVALID", f"unknown provider {provider}")

    return with_retries(_do, max_retries=max_retries, base_delay=base_delay)
