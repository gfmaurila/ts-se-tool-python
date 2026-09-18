$ErrorActionPreference="Stop"
& "$PSScriptRoot\build.ps1"
Compress-Archive -Path "dist\TS-SE-Tool-Python\*" -DestinationPath "dist\TS-SE-Tool-Python.zip" -Force
