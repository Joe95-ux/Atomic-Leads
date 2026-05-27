# Atomic Leads — Python pipeline

Local business prospecting: **Google Maps → website audit → outreach drafts**.

## Install (one venv for everything)

```bash
cd services
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -e ./atomic_models
pip install -e ./scraper
pip install -e ./analyzer
pip install -e ./outreach
pip install -e ./pipeline

# Scraper only: browser
python -m playwright install chromium
```

Copy env for outreach:

```bash
cp outreach/.env.example outreach/.env
# Set OPENAI_API_KEY, OUTREACH_SENDER_NAME
```

## Full pipeline (one command)

```bash
atomic-pipeline run -q "hair salons" -l "Austin, TX" --max 10
```

## Step by step

```bash
atomic-scrape maps -q "roofing companies" -l "Austin, TX" --max 25
atomic-audit run scraper/output/roofing-companies-austin-tx-....jsonl
atomic-outreach draft analyzer/output/roofing-...-audit-....jsonl
```

Each step writes a `.meta.json` with `artifacts` paths for the next step.

## Packages

| Package | CLI | Role |
|---------|-----|------|
| `atomic_models` | — | Shared schemas + JSONL I/O |
| `scraper` | `atomic-scrape` | Playwright / Google Maps |
| `analyzer` | `atomic-audit` | HTTP website checks |
| `outreach` | `atomic-outreach` | OpenAI email drafts |
| `pipeline` | `atomic-pipeline` | Runs all three |

## Design notes

- **One schema** (`atomic_models`) avoids drift between scraper, analyzer, and outreach.
- **Booking platforms** (Vagaro, Booksy, …) filtered at scrape time and flagged in audits.
- **Emails** use a strict no-buzzword prompt + one automatic rewrite if needed.
- **Frontend/Postgres** (`atomic-leads/`) comes later; files in `output/` import into DB when ready.
