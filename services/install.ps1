# Install all Atomic Leads Python packages into the active venv
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

pip install -e "$root/atomic_models"
pip install -e "$root/scraper"
pip install -e "$root/analyzer"
pip install -e "$root/outreach"
pip install -e "$root/pipeline"
Write-Host "Done. For scraper: python -m playwright install chromium"
