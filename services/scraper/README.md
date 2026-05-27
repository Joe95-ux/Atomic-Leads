# Atomic Scraper

Python + Playwright service that finds local businesses on **Google Maps** for the Atomic Leads outreach pipeline.

## What it collects

| Field | Source |
|-------|--------|
| Business name | Maps place page |
| Website | Maps (when listed) |
| Phone | Maps |
| Email | Usually empty — add later via website crawl |
| City / state | Parsed from address or search location |
| Address | Maps |
| Google rating & review count | Maps |
| Category | Maps |
| Maps URL & place id | Maps |

Exports **JSONL** + **CSV** under `output/` for the analyzer and (later) Postgres import.

## Setup

Requires **Python 3.11+**.

```bash
cd services/scraper
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e .
python -m playwright install chromium
# or: atomic-scrape install-browser
```

Optional: copy `.env.example` to `.env` for defaults (`SCRAPER_HEADLESS`, `SCRAPER_DELAY_MS`, etc.).

## Usage

```bash
# Headless scrape (default)
atomic-scrape maps -q "roofing companies" -l "Austin, TX" --max 25

# Watch the browser (debugging)
atomic-scrape maps -q "hair salons" -l "Dallas, TX" --max 10 --headed

# Slower / safer rate
atomic-scrape maps -q "movers" -l "Houston, TX" --max 50 --delay-ms 2500
```

Module form:

```bash
python -m atomic_scraper maps -q "restaurants" -l "San Antonio, TX" --max 20
```

## Output

Each run writes three files, e.g.:

- `output/roofing-companies-austin-tx-20260527_120000.jsonl`
- `output/roofing-companies-austin-tx-20260527_120000.csv`
- `output/roofing-companies-austin-tx-20260527_120000.meta.json`

JSONL lines are `BusinessLead` objects ready for the website analyzer step.

## Pipeline position

```
Google Maps scraper  →  website analyzer  →  AI email  →  outreach  →  CRM
        (this)         services/analyzer/
```

## Notes

- **Rate limits:** Use reasonable `--max` and `--delay-ms`. Do not run aggressive parallel scrapes against Google.
- **Selectors:** Maps UI changes; if extraction breaks, update `scrapers/google_maps.py`.
- **Compliance:** Only scrape public business listing data; include opt-out in outreach; follow CAN-SPAM/GDPR as applicable.
- **Email:** Maps rarely shows emails; the analyzer step should crawl the business website for contact pages.

## Project layout

```
services/scraper/
  pyproject.toml
  src/atomic_scraper/
    cli.py
    config.py
    models.py
    export.py
    scrapers/google_maps.py
  output/
```
