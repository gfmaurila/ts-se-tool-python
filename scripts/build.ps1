$ErrorActionPreference="Stop"
$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Ambiente virtual ausente. Execute: py -3.13 -m venv .venv"
}
& $python -m pip install -e ".[dev]"
& "$PSScriptRoot\run-tests.ps1"
& $python -m PyInstaller --noconfirm --clean --onefile --windowed --name "TS-SE-Tool" --add-data "src/tsse/infrastructure/decoder/resources;tsse/infrastructure/decoder/resources" src/tsse/desktop/main.py
Write-Host "Build em dist\TS-SE-Tool.exe"
