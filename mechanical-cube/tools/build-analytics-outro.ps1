param(
    [string]$BlenderExe = $env:BLENDER_EXE,
    [string]$OutputDirectory = '',
    [switch]$ReuseRenders
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $ProjectRoot 'output\final-analytics-v3' }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$OutputDirectory = (Resolve-Path -LiteralPath $OutputDirectory).Path
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { $Python = 'python' }
function Check-Exit([string]$Step) { if ($LASTEXITCODE -ne 0) { throw "$Step failed ($LASTEXITCODE)" } }

if (-not $ReuseRenders) {
    if (-not $BlenderExe) { $BlenderExe = (Get-Command blender -ErrorAction Stop).Source }
    & $BlenderExe --background --python (Join-Path $ProjectRoot 'scripts\render_final_analytics_v3.py') -- --out $OutputDirectory
    Check-Exit 'Dashboard render'
    & $Python (Join-Path $ProjectRoot 'scripts\render_analytics_bridge.py') --out $OutputDirectory
    Check-Exit 'Bridge render'
}
$LastFrame = Join-Path $OutputDirectory 'frames\frame_0180.png'
if (-not (Test-Path -LiteralPath $LastFrame)) { throw 'All 180 dashboard frames are required.' }
$Dashboard = Join-Path $OutputDirectory 'final-analytics-v3-clean.mp4'
ffmpeg -hide_banner -loglevel error -y -framerate 30 -i (Join-Path $OutputDirectory 'frames\frame_%04d.png') `
    -frames:v 180 -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart $Dashboard
Check-Exit 'Dashboard encoding'
$Clean = Join-Path $OutputDirectory 'analytics-outro-clean.mp4'
ffmpeg -hide_banner -loglevel error -y -i (Join-Path $OutputDirectory 'analytics-bridge-clean.mp4') -i $Dashboard `
    -filter_complex '[0:v]fps=60,settb=AVTB,setsar=1[a];[1:v]fps=60,settb=AVTB,setsar=1[b];[a][b]xfade=transition=fade:duration=1:offset=4,format=yuv420p[v]' `
    -map '[v]' -an -t 10 -r 60 -c:v libx264 -preset slow -crf 16 -movflags +faststart $Clean
Check-Exit 'Continuous outro assembly'
& $Python (Join-Path $ProjectRoot 'scripts\generate_mechanical_cube_voiceover.py') `
    --config (Join-Path $ProjectRoot 'config\analytics_outro_voiceover.json') `
    --source-video $Clean `
    --output-video (Join-Path $OutputDirectory 'analytics-outro-voiceover.mp4') `
    --voice-track (Join-Path $OutputDirectory 'analytics-outro-voiceover.wav') `
    --report (Join-Path $OutputDirectory 'analytics-outro-voiceover-report.json') `
    --parts (Join-Path $OutputDirectory 'voiceover-parts')
Check-Exit 'Narration synthesis and mixing'
Write-Host "Finished: $OutputDirectory"
