param([string]$OutputDirectory = '', [switch]$ReusePicture)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $ProjectRoot 'output\head-compact-v1' }
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { $Python = 'python' }
$RenderOptions = @('--out', $OutputDirectory)
if ($ReusePicture) { $RenderOptions += '--reuse-picture' }
& $Python (Join-Path $ProjectRoot 'scripts\build_head_compact.py') @RenderOptions
if ($LASTEXITCODE -ne 0) { throw 'Shots 01-18 compact preview failed' }
Write-Host "83-second review: $OutputDirectory"
