# Daily Chinese News Brief

This project generates a high-signal Chinese daily news briefing from the previous 24 hours.

It collects candidate news from Google News RSS, GDELT, filtered Federal Reserve monetary policy RSS, and filtered BLS economic release RSS. It removes obvious low-value stories, deduplicates similar headlines, uses OpenAI to rank and summarize the strongest stories in Simplified Chinese, includes the VIX index, renders a mobile-friendly HTML email, and sends it through SMTP.

The goal is quality, not coverage. The briefing includes at most 10 stories and should be readable in under 5 minutes.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Required variables:

```text
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
MAX_STORIES=10
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_smtp_username
EMAIL_PASSWORD=your_smtp_password
EMAIL_TO=recipient@example.com
EMAIL_FROM=sender@example.com
# Optional: WeChat push via PushPlus (https://www.pushplus.plus). Leave empty to skip.
PUSHPLUS_TOKEN=
```

Use an app password if your email provider requires one.

## WeChat push (optional)

To receive the briefing on WeChat in addition to email, use [Server酱 (方糖)](https://sct.ftqq.com) — it is free to start:

1. Open [sct.ftqq.com](https://sct.ftqq.com), log in by scanning the QR code with WeChat, and follow the Server酱 WeChat official account.
2. Copy your SendKey and set it as `SERVERCHAN_SENDKEY` in `.env` (and as a GitHub secret if using Actions).
3. When the briefing is generated, the workflow sends the same content to your WeChat right after the email.

The free tier allows several pushes per day, which is enough for one briefing plus occasional major-event alerts. (A PushPlus token is still accepted via `PUSHPLUS_TOKEN`, but that service requires paid real-name verification to send messages.)

## Major Breaking Event Alerts (optional)

`breaking_events.yml` runs every hour and watches for sudden, historically major international events — for example a major power suddenly launching a war or large-scale military attack, a nuclear incident, or a catastrophic global event. When such an event is detected, it sends an immediate WeChat alert via PushPlus. The alert threshold is deliberately very strict: routine diplomacy, isolated incidents, and widely anticipated actions are ignored, and each event is alerted only once.

It uses the same `OPENAI_*` and `PUSHPLUS_TOKEN` secrets as the daily briefing. Notified events are persisted in `state/notified_breaking.json` and pruned after 14 days.

## Use DeepSeek instead of OpenAI

The pipeline uses the OpenAI SDK, which is also compatible with DeepSeek's API. To switch models, set these values in `.env`:

```text
OPENAI_API_KEY=your_deepseek_api_key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-flash
```

`deepseek-v4-flash` is the non-thinking mode (the successor to the deprecated `deepseek-chat`). Use `deepseek-v4-pro` if you want the thinking mode. If you keep using OpenAI, leave `OPENAI_BASE_URL` empty and set `OPENAI_MODEL` to a model such as `gpt-4o-mini`.

When running through GitHub Actions, also add `OPENAI_BASE_URL` as a repository secret.

## Test Locally

Run a dry-run to generate an HTML preview without sending email:

```bash
python -m src.main --dry-run
```

This writes `daily_news_preview.html` and prints collection counts. If `OPENAI_API_KEY` is missing, dry-run still creates a preview using a local heuristic fallback so you can verify collection, filtering, VIX, and rendering. For production quality ranking and Chinese summarization, configure OpenAI.

To send the email locally:

```bash
python -m src.main
```

## GitHub Secrets

Add these repository secrets in GitHub:

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
MAX_STORIES
EMAIL_HOST
EMAIL_PORT
EMAIL_USER
EMAIL_PASSWORD
EMAIL_TO
EMAIL_FROM
SERVERCHAN_SENDKEY
PUSHPLUS_TOKEN
```

`OPENAI_MODEL` can be `gpt-4o-mini` for a cost-efficient first version.

## GitHub Actions Schedule

The workflow is in `.github/workflows/daily_news.yml` and is already configured to run daily at `20:00 Beijing Time` (`12:00 UTC`):

```yaml
on:
  schedule:
    - cron: "0 12 * * *"
  workflow_dispatch:
```

GitHub Actions scheduled workflows may start a few minutes later than the configured cron time. You can also trigger a run manually from the GitHub Actions tab through `workflow_dispatch`. To change the time, edit the cron expression in the workflow file. The briefing covers the previous 24 hours.

## First-Version Limitations

Google News RSS links may point through Google redirect URLs instead of direct publisher URLs.

The system ranks candidates from titles, snippets, sources, and links only. It does not fetch full article text, which keeps OpenAI usage low but can miss nuance.

GDELT and RSS results can vary by availability and upstream ranking. Google News RSS descriptions usually repeat the headline instead of providing article text, so headline-only stories receive shorter summaries to avoid unsupported filler.

Federal Reserve and BLS feeds use strict local filters. Routine Fed minutes and smaller economic data moves do not automatically enter the candidate pool.

The project intentionally omits weak stories instead of filling the email.
