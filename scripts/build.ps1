$ErrorActionPreference="Stop"
$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Ambiente virtual ausente. Execute: py -3.13 -m venv .venv"
}
& $python -m pip install -e ".[dev]"
& "$PSScriptRoot\run-tests.ps1"
& $python -m PyInstaller --noconfirm --clean --windowed --name "TS-SE-Tool-Python" src/tsse/desktop/main.py
Write-Host "Build em dist\TS-SE-Tool-Python"
