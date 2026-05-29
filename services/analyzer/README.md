# Atomic Analyzer

Audits business websites from **scraper JSONL** output and produces sales-ready issue lists for outreach.

## Checks

### Core (homepage)

| Issue | What it detects |
|-------|-----------------|
| Chain / franchise | Corporate locator pages (Hair Cuttery, Sola, etc.) |
| Social only | Facebook/Instagram instead of owned site |
| Third-party booking | Vagaro, Booksy, etc. |
| No SSL / unreachable / slow | Technical basics |
| Title, meta description, viewport | SEO + mobile hints |
| CTA, H1, homepage forms | Conversion + on-page SEO |

### P1 (depth, still lightweight)

| Issue | What it detects |
|-------|-----------------|
| **no_local_business_schema** | JSON-LD exists but no `LocalBusiness` / `HairSalon` type |
| **wordpress_detected** | WordPress site (maintenance pitch angle) |
| **outdated_copyright** | Footer copyright 2+ years old |
| **Contact page** | Fetches `/contact`, `/contact-us`, etc. |
| **contact_page_broken_form** | Misconfigured form on contact page |
| **contact_page_no_form** | Contact page with no form or email |
| **no_contact_page** | No working contact URL found |

Contact email is discovered during the same contact-page pass.

## Setup

```bash
cd services
.venv\Scripts\activate
pip install -e ./atomic_models -e ./analyzer
```

## Usage

```bash
atomic-audit run ../scraper/output/your-scrape.jsonl
atomic-audit one -u "https://example.com" -n "Example Co"
```

## Output

- `output/*-audit-*.jsonl` — full reports + `metrics` (wordpress, copyright, contact URL, etc.)
- `output/*-summary.json` — compact view with `pitch_type`, `contact_email`
- `output/*.meta.json` — run stats

## Pipeline

```
atomic-scrape maps  →  atomic-audit run  →  atomic-outreach draft
```
