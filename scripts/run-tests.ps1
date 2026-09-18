$ErrorActionPreference="Stop"
$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "py" }

& $python -m ruff check src tests
if ($LASTEXITCODE -ne 0) { throw "Quality gate failed: Ruff" }

& $python -m mypy src
if ($LASTEXITCODE -ne 0) { throw "Quality gate failed: mypy" }

& $python -m pytest -q --cov=src/tsse --cov-report=term-missing
if ($LASTEXITCODE -ne 0) { throw "Quality gate failed: pytest" }
