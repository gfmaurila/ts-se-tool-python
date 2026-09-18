$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
python -m ruff check src tests
python -m mypy src
python -m pytest -q --cov=tsse --cov-report=term-missing
