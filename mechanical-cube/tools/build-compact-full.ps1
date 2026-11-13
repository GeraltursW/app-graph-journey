param(
    [string]$OutputDirectory = '',
    [switch]$RebuildHead,
    [switch]$RebuildMechanical
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $ProjectRoot 'output\compact-full-v1.15' }
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$OutputDirectory = (Resolve-Path -LiteralPath $OutputDirectory).Path
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { $Python = 'python' }
$Head = Join-Path $ProjectRoot 'releases\latest\compact-head'
$Mechanical = Join-Path $ProjectRoot 'releases\latest\compact-mechanical'
if (Test-Path -LiteralPath (Join-Path $OutputDirectory 'head\timeline.json')) { $Head = Join-Path $OutputDirectory 'head' }
if (Test-Path -LiteralPath (Join-Path $OutputDirectory 'mechanical\timeline.json')) { $Mechanical = Join-Path $OutputDirectory 'mechanical' }
$HeadConfig = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $ProjectRoot 'config\head_compact.json') | ConvertFrom-Json
$MechanicalConfig = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $ProjectRoot 'config\mechanical_compact.json') | ConvertFrom-Json
$HeadTimeline = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $Head 'timeline.json') | ConvertFrom-Json
$MechanicalTimeline = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $Mechanical 'timeline.json') | ConvertFrom-Json
if ($HeadTimeline.revision -ne $HeadConfig.revision) { $RebuildHead = $true }
if ($MechanicalTimeline.revision -ne $MechanicalConfig.revision) { $RebuildMechanical = $true }
function Check-Exit([string]$Step) { if ($LASTEXITCODE -ne 0) { throw "$Step failed" } }
if ($RebuildMechanical) {
    $Mechanical = Join-Path $OutputDirectory 'mechanical'
    & $Python (Join-Path $ProjectRoot 'scripts\build_mechanical_compact.py') --out $Mechanical
    Check-Exit 'Mechanical rebuild'
}
if ($RebuildHead -or $RebuildMechanical) {
    $Head = Join-Path $OutputDirectory 'head'
    & $Python (Join-Path $ProjectRoot 'scripts\build_head_compact.py') --out $Head --mechanical (Join-Path $Mechanical 'mechanical-compact-clean.mp4')
    Check-Exit 'Head rebuild'
}
& $Python (Join-Path $ProjectRoot 'scripts\build_compact_full_film.py') --head-dir $Head --mechanical-dir $Mechanical --out $OutputDirectory
Check-Exit 'Complete film assembly'
& $Python (Join-Path $ProjectRoot 'scripts\validate_compact_full_film.py') --out $OutputDirectory
Check-Exit 'Complete film validation'
Write-Host "v1.15.0 complete film: $OutputDirectory"
