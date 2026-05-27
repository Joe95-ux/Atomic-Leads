# Atomic Analyzer

Audits business websites from **scraper JSONL** output and produces sales-ready issue lists for outreach.

## Checks (v0)

| Issue | What it detects |
|-------|-----------------|
| No website | Missing URL on Maps listing |
| Third-party booking | Vagaro, Booksy, etc. instead of owned site |
| No SSL | HTTP-only or HTTPS failure |
| Unreachable | Timeout / connection errors |
| Slow response | Homepage slower than threshold (default 3s) |
| Missing meta description | SEO gap |
| Missing / weak title | SEO gap |
| Not mobile optimized | No viewport meta tag |
| No schema | No JSON-LD structured data |
| No CTA | No contact/book/quote links or buttons |
| Broken forms | Forms with empty/`#` actions |
| Missing / multiple H1 | Basic on-page SEO |

Each business gets a **score 0–100** (lower = more issues to fix = stronger pitch).

## Setup

```bash
cd services/analyzer
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e .
```

## Usage

```bash
# Audit a scraper run
atomic-audit run ../scraper/output/hair-salons-austin-tx-20260527-033213.jsonl

# Single URL smoke test
atomic-audit one -u "https://example.com" -n "Example Co"
```

## Output

For input `hair-salons-....jsonl`:

- `output/hair-salons-...-audit-TIMESTAMP.jsonl` — full reports (for DB / AI step)
- `output/hair-salons-...-audit-TIMESTAMP-summary.json` — compact `{ business, website, issues, score }`
- `output/...-meta.json` — run stats

### Example summary entry

```json
{
  "business": "ABC Roofing",
  "website": "https://abcroofing.com",
  "issues": [
    "Missing meta description",
    "Missing viewport meta tag (likely poor mobile experience)",
    "No schema.org structured data found"
  ],
  "score": 71
}
```

## Pipeline

```
atomic-scrape maps  →  atomic-audit run  →  AI email (next)  →  outreach
```

## Notes

- Analyzer uses **HTTP + BeautifulSoup** (fast). No browser required.
- Booking platforms are flagged so you do not pitch “website redesign” to a Vagaro link.
- Email discovery from website contact pages can be a later enhancement.
