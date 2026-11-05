param([string]$OutputDirectory = '', [switch]$SkipRender, [switch]$SkipNarration)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $ProjectRoot 'output\scenario-path-v1' }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$OutputDirectory = (Resolve-Path -LiteralPath $OutputDirectory).Path
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { $Python = 'python' }
function Check-Exit([string]$Step) { if ($LASTEXITCODE -ne 0) { throw "$Step failed" } }
if (-not $SkipRender) {
    & $Python (Join-Path $ProjectRoot 'scripts\render_friends_scenario.py') --out $OutputDirectory
    Check-Exit 'Scenario rendering'
}
if (-not $SkipNarration) {
    & $Python (Join-Path $ProjectRoot 'scripts\generate_mechanical_cube_voiceover.py') `
    --config (Join-Path $ProjectRoot 'config\scenario_path_voiceover.json') `
    --source-video (Join-Path $OutputDirectory 'scenario-path-clean.mp4') `
    --output-video (Join-Path $OutputDirectory 'scenario-path-voiceover.mp4') `
    --voice-track (Join-Path $OutputDirectory 'scenario-path-voiceover.wav') `
    --report (Join-Path $OutputDirectory 'voiceover-report.json') `
    --parts (Join-Path $OutputDirectory 'voiceover-parts')
    Check-Exit 'Scenario narration'
}
Copy-Item -LiteralPath (Join-Path $OutputDirectory 'scenario-path-clean.mp4') -Destination (Join-Path $ProjectRoot 'releases\latest\scenario-path-clean.mp4') -Force
Copy-Item -LiteralPath (Join-Path $OutputDirectory 'scenario-case-clean.mp4') -Destination (Join-Path $ProjectRoot 'releases\latest\scenario-case-clean.mp4') -Force
Copy-Item -LiteralPath (Join-Path $OutputDirectory 'scenario-path-voiceover.wav') -Destination (Join-Path $ProjectRoot 'assets\audio\scenario-path-voiceover.wav') -Force
& $Python (Join-Path $ProjectRoot 'scripts\integrate_scenario_path.py') --output (Join-Path $OutputDirectory 'application-knowledge-graph-scenario.mp4')
Check-Exit 'Full-film assembly'
& $Python (Join-Path $ProjectRoot 'scripts\integrate_scenario_path.py') `
    --source (Join-Path $ProjectRoot 'releases\iterations\12-app-graph-data-continuous-music-v1.6.mp4') `
    --preserve-source-music --output (Join-Path $OutputDirectory 'application-knowledge-graph-and-data-scenario.mp4')
Check-Exit 'Standalone main film assembly'
& $Python (Join-Path $ProjectRoot 'scripts\smooth_scenario_transitions.py') `
    --source (Join-Path $OutputDirectory 'application-knowledge-graph-and-data-scenario.mp4') `
    --out (Join-Path $OutputDirectory 'smooth-transitions') `
    --output (Join-Path $OutputDirectory 'application-knowledge-graph-and-data-smooth.mp4')
Check-Exit 'Main-film smooth transitions'
& $Python (Join-Path $ProjectRoot 'scripts\smooth_scenario_transitions.py') `
    --source (Join-Path $OutputDirectory 'application-knowledge-graph-scenario.mp4') `
    --out (Join-Path $OutputDirectory 'smooth-transitions') --reuse-transitions `
    --output (Join-Path $OutputDirectory 'application-knowledge-graph-mechanical-smooth.mp4')
Check-Exit 'Integrated-film smooth transitions'
& $Python (Join-Path $ProjectRoot 'scripts\integrate_page_exploration.py') `
    --source (Join-Path $OutputDirectory 'application-knowledge-graph-and-data-smooth.mp4') `
    --output (Join-Path $OutputDirectory 'application-knowledge-graph-and-data-final.mp4')
Check-Exit 'Main-film page exploration update'
& $Python (Join-Path $ProjectRoot 'scripts\integrate_page_exploration.py') `
    --source (Join-Path $OutputDirectory 'application-knowledge-graph-mechanical-smooth.mp4') `
    --output (Join-Path $OutputDirectory 'application-knowledge-graph-mechanical-final.mp4')
Check-Exit 'Integrated-film page exploration update'
