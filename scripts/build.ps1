$ErrorActionPreference="Stop"
python -m pip install -e ".[dev]"
& "$PSScriptRoot\run-tests.ps1"
python -m PyInstaller --noconfirm --clean --windowed --name "TS-SE-Tool-Python" src/tsse/desktop/main.py
Write-Host "Build em dist\TS-SE-Tool-Python"
