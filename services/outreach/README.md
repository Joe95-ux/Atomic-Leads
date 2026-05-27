# Atomic Outreach

Turns **audit JSONL** into short, human-sounding cold email drafts (OpenAI).

## Tone

- Plain language, no agency buzzwords
- 1–2 real issues from the audit
- Soft CTA (call or short Loom), not pushy
- Auto-rewrite if banned phrases slip through

## Setup

```bash
cd services/outreach
cp .env.example .env   # add OPENAI_API_KEY, your name for sign-off
pip install -e ../atomic_models
pip install -e .
```

## Usage

```bash
atomic-outreach draft ../analyzer/output/your-audit-file.jsonl
atomic-outreach preview ../analyzer/output/your-audit-file.jsonl -i 0
```

Outputs:

- `*.jsonl` — structured drafts (for sending layer later)
- `*.txt` — copy-paste friendly
- `*.meta.json` — run stats + artifact paths

## Env

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Required |
| `OUTREACH_SENDER_NAME` | Sign-off name |
| `OUTREACH_SENDER_ROLE` | One line about what you do |
| `OUTREACH_MODEL` | Default `gpt-4o-mini` |
