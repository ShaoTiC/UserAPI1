"""CLI entrypoint for the World Cup schedule email agent.

Examples:

  # Dry-run: write an .eml + HTML preview under ./out
  python -m world_cup_email_agent

  # Next 2 days of fixtures
  python -m world_cup_email_agent --mode window --days 2

  # Remaining tournament fixtures
  python -m world_cup_email_agent --mode upcoming

  # Actually send via SMTP (requires env vars; see .env.example)
  WC_DRY_RUN=0 SMTP_HOST=smtp.qq.com SMTP_PORT=465 \\
    SMTP_USERNAME=you@qq.com SMTP_PASSWORD=auth_code \\
    WC_EMAIL_TO=3461630168@qq.com \\
    python -m world_cup_email_agent --send

  # Keep running and email once per day
  python -m world_cup_email_agent --loop --interval-hours 24
"""

from __future__ import annotations

import argparse
import sys

from .agent import WorldCupEmailAgent
from .config import AgentConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="world_cup_email_agent",
        description="Email FIFA World Cup 2026 match schedules automatically.",
    )
    parser.add_argument(
        "--mode",
        choices=("window", "upcoming", "all-remaining"),
        default="window",
        help="window = next N days (default); upcoming/all-remaining = rest of tournament",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Lookahead days for --mode window (default: WC_LOOKAHEAD_DAYS or 3)",
    )
    parser.add_argument(
        "--to",
        dest="recipient",
        default=None,
        help="Recipient email (default: WC_EMAIL_TO or 3461630168@qq.com)",
    )
    parser.add_argument(
        "--timezone",
        default=None,
        help="Display timezone (default: WC_TIMEZONE or Asia/Shanghai)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for dry-run .eml/.html files (default: out/)",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Attempt real SMTP delivery (requires SMTP_* env vars; disables dry-run)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry-run even if SMTP credentials are present",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Keep running and send on an interval",
    )
    parser.add_argument(
        "--interval-hours",
        type=float,
        default=24.0,
        help="Hours between sends when --loop is set (default: 24)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    dry_run: bool | None
    if args.dry_run:
        dry_run = True
    elif args.send:
        dry_run = False
    else:
        dry_run = None

    overrides: dict[str, object] = {
        "recipient": args.recipient,
        "timezone": args.timezone,
        "output_dir": args.output_dir,
        "dry_run": dry_run,
    }
    if args.days is not None:
        overrides["lookahead_days"] = args.days
    config = AgentConfig.from_env(**overrides)

    agent = WorldCupEmailAgent(config)

    if args.loop:
        print(
            f"Starting loop every {args.interval_hours}h → {config.recipient} "
            f"(dry_run={config.dry_run}, can_send={config.can_send})"
        )
        try:
            agent.run_forever(interval_hours=args.interval_hours, mode=args.mode)
        except KeyboardInterrupt:
            print("Stopped.")
            return 0
        return 0

    result = agent.run(mode=args.mode, days=args.days)
    print(result.draft.subject)
    print(f"Matches: {result.match_count}")
    print(f"To: {result.delivery.recipient}")
    print(f"Delivery: {result.delivery.mode}")
    if result.delivery.path:
        print(result.delivery.detail)
    elif result.delivery.detail:
        print(result.delivery.detail)
    print()
    print(result.draft.text_body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
