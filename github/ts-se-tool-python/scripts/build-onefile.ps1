$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
python -m pip install -e ".[dev]"
python -m ruff check src tests
python -m mypy src
python -m pytest -q
if (-not (Test-Path "src/tsse/desktop/main.py")) { throw "src/tsse/desktop/main.py ainda não existe. Execute as tasks de implementação." }
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "TS-SE-Tool" --paths src src/tsse/desktop/main.py
if (-not (Test-Path "dist/TS-SE-Tool.exe")) { throw "Build não gerou dist/TS-SE-Tool.exe" }
Write-Host "OK: $Root\dist\TS-SE-Tool.exe"
