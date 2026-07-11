# FIFA World Cup 2026 — Schedule Email Agent

Python agent that fetches the live World Cup 2026 match schedule and emails you
a digest (HTML + plain text). Defaults to dry-run so you can preview safely.

## What it does

1. Pulls fixtures from the public [wheniskickoff.com](https://wheniskickoff.com/data/) JSON API (no API key).
2. Filters to the next N days (default 3) or the remaining tournament.
3. Builds a bilingual-friendly schedule email with local kickoff times.
4. Sends via SMTP, or writes `.eml` + `.html` previews when dry-run is on.

Default recipient: `3461630168@qq.com` (override with `--to` / `WC_EMAIL_TO`).

## Quick start (dry-run)

```bash
python -m world_cup_email_agent
```

Artifacts land in `out/`:

- `world-cup-schedule-*.eml` — full MIME email
- `world-cup-schedule-*.html` — browser preview

```bash
# Next 2 days
python -m world_cup_email_agent --mode window --days 2

# All remaining fixtures
python -m world_cup_email_agent --mode upcoming
```

## Send real email (QQ Mail)

1. Copy `.env.example` and fill in an SMTP authorization code (not your QQ login password).
2. Export the variables, then run with `--send`:

```bash
export WC_DRY_RUN=0
export SMTP_HOST=smtp.qq.com
export SMTP_PORT=465
export SMTP_USE_SSL=1
export SMTP_USERNAME=3461630168@qq.com
export SMTP_PASSWORD='your_authorization_code'
export WC_EMAIL_FROM=3461630168@qq.com
export WC_EMAIL_TO=3461630168@qq.com

python -m world_cup_email_agent --send --mode window --days 3
```

Gmail works the same way with `SMTP_HOST=smtp.gmail.com` and an app password.

## Run automatically every day

### Option A — agent loop

```bash
python -m world_cup_email_agent --send --loop --interval-hours 24 --mode window --days 3
```

### Option B — cron (recommended on a server)

```cron
0 8 * * * cd /path/to/UserAPI1 && \
  . ./venv/bin/activate && \
  set -a && . ./.env && set +a && \
  python -m world_cup_email_agent --send --mode window --days 3 \
  >> /var/log/world-cup-email-agent.log 2>&1
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Layout

```
world_cup_email_agent/
  agent.py       # orchestration + optional forever loop
  schedule.py    # fetch + filter fixtures
  emailer.py     # HTML/text compose + SMTP / dry-run delivery
  config.py      # env-based settings
  __main__.py    # CLI
```

No third-party packages required (Python 3.10+).
