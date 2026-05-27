#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
pip install -e "$ROOT/atomic_models"
pip install -e "$ROOT/scraper"
pip install -e "$ROOT/analyzer"
pip install -e "$ROOT/outreach"
pip install -e "$ROOT/pipeline"
echo "Done. For scraper: python -m playwright install chromium"
