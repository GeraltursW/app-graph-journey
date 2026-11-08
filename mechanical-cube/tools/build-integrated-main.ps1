param([string]$OutputDirectory = '', [switch]$RebuildScenario)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $ProjectRoot 'output\integrated-main-v1.10' }
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { $Python = 'python' }
$SceneSource = Join-Path $ProjectRoot 'releases\latest\scenario-context-clean.mp4'
if ($RebuildScenario) {
    $SceneOutput = Join-Path $OutputDirectory 'scenario'
    & (Join-Path $PSScriptRoot 'build-scenario-context.ps1') -OutputDirectory $SceneOutput
    $SceneSource = Join-Path $SceneOutput 'scenario-context-clean.mp4'
}
& $Python (Join-Path $ProjectRoot 'scripts\integrate_scenario_main.py') --out $OutputDirectory --scene-source $SceneSource
if ($LASTEXITCODE -ne 0) { throw 'Main film integration failed' }
Write-Host "Complete subtitled main film: $OutputDirectory"
