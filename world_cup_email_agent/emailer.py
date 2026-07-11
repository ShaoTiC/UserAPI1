"""Compose and deliver World Cup schedule emails."""

from __future__ import annotations

import smtplib
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from html import escape
from pathlib import Path
from typing import Sequence

from .config import AgentConfig
from .schedule import Match, group_by_local_date


@dataclass(frozen=True)
class EmailDraft:
    """A ready-to-send email payload."""

    subject: str
    text_body: str
    html_body: str
    recipient: str
    sender: str


@dataclass(frozen=True)
class DeliveryResult:
    """Outcome of an email delivery attempt."""

    mode: str
    recipient: str
    subject: str
    path: str | None = None
    detail: str = ""


def build_email(
    matches: Sequence[Match],
    config: AgentConfig,
    *,
    title: str | None = None,
    generated_at: datetime | None = None,
) -> EmailDraft:
    """Build a plain-text + HTML schedule email."""

    now = generated_at or datetime.now(timezone.utc)
    heading = title or _default_title(matches, config)
    subject = heading

    text_body = _render_text(matches, config, heading=heading, generated_at=now)
    html_body = _render_html(matches, config, heading=heading, generated_at=now)
    sender = config.sender_email or config.smtp_username or "world-cup-agent@localhost"

    return EmailDraft(
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        recipient=config.recipient,
        sender=sender,
    )


def deliver(draft: EmailDraft, config: AgentConfig) -> DeliveryResult:
    """Send via SMTP, or write a dry-run artifact when sending is disabled."""

    if config.can_send:
        _send_smtp(draft, config)
        return DeliveryResult(
            mode="smtp",
            recipient=draft.recipient,
            subject=draft.subject,
            detail=f"Sent through {config.smtp_host}:{config.smtp_port}",
        )

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"world-cup-schedule-{stamp}.eml"
    path.write_text(_as_eml(draft, config), encoding="utf-8")

    preview = output_dir / f"world-cup-schedule-{stamp}.html"
    preview.write_text(draft.html_body, encoding="utf-8")

    reason = "dry-run" if config.dry_run else "missing SMTP credentials"
    return DeliveryResult(
        mode=reason,
        recipient=draft.recipient,
        subject=draft.subject,
        path=str(path),
        detail=f"Saved email draft to {path} (HTML preview: {preview})",
    )


def _default_title(matches: Sequence[Match], config: AgentConfig) -> str:
    if not matches:
        return "FIFA World Cup 2026 — no upcoming matches"
    first = matches[0].local_kickoff(config.timezone).strftime("%b %d")
    last = matches[-1].local_kickoff(config.timezone).strftime("%b %d")
    if first == last:
        return f"FIFA World Cup 2026 — {len(matches)} match(es) on {first}"
    return f"FIFA World Cup 2026 — {len(matches)} match(es) {first}–{last}"


def _render_text(
    matches: Sequence[Match],
    config: AgentConfig,
    *,
    heading: str,
    generated_at: datetime,
) -> str:
    lines = [
        heading,
        "=" * len(heading),
        "",
        f"Timezone: {config.timezone}",
        f"Generated (UTC): {generated_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        "",
    ]
    if not matches:
        lines.append("No matches found for this window.")
        lines.append("")
        lines.append("Source: wheniskickoff.com World Cup 2026 schedule.")
        return "\n".join(lines)

    for day, day_matches in group_by_local_date(matches, config.timezone):
        lines.append(day.strftime("%A, %B %d, %Y"))
        lines.append("-" * 32)
        for match in day_matches:
            local = match.local_kickoff(config.timezone)
            venue = match.venue
            if match.city:
                venue = f"{match.venue} ({match.city})"
            score = ""
            if match.is_finished and match.score_home is not None and match.score_away is not None:
                score = f"  [{match.score_home}-{match.score_away}]"
            lines.append(
                f"{local.strftime('%H:%M')}  {match.matchup}{score}"
            )
            lines.append(f"         {match.phase_label} · {venue}")
            lines.append("")
        lines.append("")

    lines.append("Source: wheniskickoff.com World Cup 2026 schedule.")
    lines.append("Sent by World Cup Schedule Agent.")
    return "\n".join(lines)


def _render_html(
    matches: Sequence[Match],
    config: AgentConfig,
    *,
    heading: str,
    generated_at: datetime,
) -> str:
    rows: list[str] = []
    if not matches:
        rows.append("<p style=\"margin:0;color:#445;\">No matches found for this window.</p>")
    else:
        for day, day_matches in group_by_local_date(matches, config.timezone):
            rows.append(
                f"<h2 style=\"margin:24px 0 8px;font-size:16px;color:#0b3d2e;\">"
                f"{escape(day.strftime('%A, %B %d, %Y'))}</h2>"
            )
            rows.append(
                "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" "
                "style=\"border-collapse:collapse;width:100%;\">"
            )
            for match in day_matches:
                local = match.local_kickoff(config.timezone)
                venue = match.venue
                if match.city:
                    venue = f"{match.venue} · {match.city}"
                score_html = ""
                if (
                    match.is_finished
                    and match.score_home is not None
                    and match.score_away is not None
                ):
                    score_html = (
                        f"<span style=\"color:#666;font-size:13px;\">"
                        f" ({match.score_home}-{match.score_away})</span>"
                    )
                rows.append(
                    "<tr>"
                    f"<td style=\"padding:12px 0;border-bottom:1px solid #e6efe9;"
                    f"vertical-align:top;width:72px;font-weight:700;color:#0b3d2e;\">"
                    f"{escape(local.strftime('%H:%M'))}</td>"
                    "<td style=\"padding:12px 0;border-bottom:1px solid #e6efe9;\">"
                    f"<div style=\"font-size:16px;font-weight:600;color:#102a43;\">"
                    f"{escape(match.matchup)}{score_html}</div>"
                    f"<div style=\"margin-top:4px;font-size:13px;color:#486581;\">"
                    f"{escape(match.phase_label)} · {escape(venue)}</div>"
                    "</td></tr>"
                )
            rows.append("</table>")

    generated = generated_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>{escape(heading)}</title></head>
<body style="margin:0;padding:0;background:#f3f7f4;font-family:Georgia,'Times New Roman',serif;">
  <div style="max-width:640px;margin:0 auto;padding:24px 16px;">
    <div style="background:linear-gradient(135deg,#0b3d2e,#1f7a5c);color:#fff;padding:28px 24px;border-radius:4px 4px 0 0;">
      <div style="font-size:12px;letter-spacing:0.12em;text-transform:uppercase;opacity:0.85;">FIFA World Cup 2026</div>
      <h1 style="margin:8px 0 0;font-size:24px;line-height:1.3;">{escape(heading)}</h1>
      <p style="margin:10px 0 0;font-size:14px;opacity:0.9;">Times shown in {escape(config.timezone)}</p>
    </div>
    <div style="background:#ffffff;padding:8px 24px 24px;border:1px solid #d9e8df;border-top:0;border-radius:0 0 4px 4px;">
      {''.join(rows)}
      <p style="margin:28px 0 0;font-size:12px;color:#829ab1;">
        Generated {escape(generated)}. Source: wheniskickoff.com.
      </p>
    </div>
  </div>
</body>
</html>
"""


def _as_eml(draft: EmailDraft, config: AgentConfig) -> str:
    message = _build_message(draft, config)
    return message.as_string()


def _build_message(draft: EmailDraft, config: AgentConfig) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = draft.subject
    message["From"] = f"{config.sender_name} <{draft.sender}>"
    message["To"] = draft.recipient
    message.set_content(draft.text_body)
    message.add_alternative(draft.html_body, subtype="html")
    return message


def _send_smtp(draft: EmailDraft, config: AgentConfig) -> None:
    message = _build_message(draft, config)
    if config.smtp_use_ssl:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, context=context) as server:
            server.login(config.smtp_username, config.smtp_password)
            server.send_message(message)
        return

    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as server:
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
        server.login(config.smtp_username, config.smtp_password)
        server.send_message(message)
