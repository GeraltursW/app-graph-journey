param(
    [Parameter(Mandatory=$true)][string]$BlenderExe,
    [string]$OutputDirectory = ''
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $ProjectRoot 'output\page-exploration' }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$OutputDirectory = (Resolve-Path -LiteralPath $OutputDirectory).Path
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { $Python = 'python' }
function Check-Exit([string]$Step) { if ($LASTEXITCODE -ne 0) { throw "$Step failed" } }
& $BlenderExe -b (Join-Path $ProjectRoot 'blender\page-exploration.blend') `
    --python (Join-Path $ProjectRoot 'scripts\render_page_exploration.py') `
    -- --out (Join-Path $OutputDirectory 'frames')
Check-Exit 'Page exploration render'
$Shot = Join-Path $ProjectRoot 'releases\latest\page-exploration-clean.mp4'
& ffmpeg -hide_banner -loglevel error -y -framerate 30 `
    -i (Join-Path $OutputDirectory 'frames\frame_%04d.png') `
    -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart $Shot
Check-Exit 'Page exploration encoding'
& $Python (Join-Path $ProjectRoot 'scripts\generate_mechanical_cube_voiceover.py') `
    --config (Join-Path $ProjectRoot 'config\page_exploration_voiceover.json') `
    --source-video $Shot --output-video (Join-Path $OutputDirectory 'narration-review.mp4') `
    --voice-track (Join-Path $ProjectRoot 'assets\audio\page-exploration-voiceover.wav') `
    --report (Join-Path $OutputDirectory 'voiceover-report.json') `
    --parts (Join-Path $OutputDirectory 'voiceover-parts')
Check-Exit 'Page exploration narration'
