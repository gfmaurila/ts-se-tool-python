$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Exe = Join-Path $Root "dist\TS-SE-Tool.exe"
if (-not (Test-Path $Exe)) { throw "Execute build-onefile.ps1 primeiro." }
$p = Start-Process -FilePath $Exe -PassThru
Start-Sleep -Seconds 5
if ($p.HasExited -and $p.ExitCode -ne 0) { throw "EXE encerrou com código $($p.ExitCode)." }
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }
Write-Host "Smoke test de inicialização concluído."
