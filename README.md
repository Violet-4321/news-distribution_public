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
```

Use an app password if your email provider requires one.

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
