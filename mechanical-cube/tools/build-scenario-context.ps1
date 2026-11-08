param([string]$OutputDirectory = '', [switch]$StillsOnly)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $ProjectRoot 'output\scenario-context-v1' }
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { $Python = 'python' }
& $Python (Join-Path $ProjectRoot 'scripts\prepare_scenario_context.py')
if ($LASTEXITCODE -ne 0) { throw 'Narration preparation failed' }
$RenderOptions = @('--out', $OutputDirectory)
if ($StillsOnly) { $RenderOptions += '--stills-only' }
& $Python (Join-Path $ProjectRoot 'scripts\render_scenario_context.py') @RenderOptions
if ($LASTEXITCODE -ne 0) { throw 'Scenario context rendering failed' }
if (-not $StillsOnly) {
    & $Python (Join-Path $ProjectRoot 'scripts\export_student_preview.py') --out $OutputDirectory
    if ($LASTEXITCODE -ne 0) { throw 'Student example export failed' }
}
Write-Host "Scenario context preview: $OutputDirectory"
