param(
    [string]$OutputDirectory = '',
    [string]$MainSource = '',
    [string]$MechanicalSource = '',
    [switch]$ReuseRenders
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $ProjectRoot 'output\final-delivery' }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$OutputDirectory = (Resolve-Path -LiteralPath $OutputDirectory).Path
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { $Python = 'python' }
function Check-Exit([string]$Step) { if ($LASTEXITCODE -ne 0) { throw "$Step failed" } }
$Mechanical = Join-Path $OutputDirectory 'mechanical'
$Outro = Join-Path $OutputDirectory 'outro'
New-Item -ItemType Directory -Path $Mechanical,$Outro -Force | Out-Null
if ($ReuseRenders) {
    foreach ($Name in @('mechanical-natural-clean.mp4','mechanical-natural-voiceover.wav','chapter-natural-clean.mp4')) {
        Copy-Item -LiteralPath (Join-Path $ProjectRoot "releases\latest\$Name") -Destination (Join-Path $Mechanical $Name) -Force
    }
    Copy-Item -LiteralPath (Join-Path $ProjectRoot 'releases\latest\analytics-outro-typography-clean.mp4') -Destination (Join-Path $Outro 'analytics-outro-clean.mp4') -Force
} else {
    & $Python (Join-Path $ProjectRoot 'scripts\prepare_natural_mechanical.py')
    Check-Exit 'Natural narration'
    & $Python (Join-Path $ProjectRoot 'scripts\render_mechanical_natural.py') --out $Mechanical
    Check-Exit 'Mechanical rendering'
    & $Python (Join-Path $ProjectRoot 'scripts\render_analytics_bridge.py') --source (Join-Path $Mechanical 'mechanical-natural-clean.mp4') --out $Outro
    Check-Exit 'New outro bridge'
    & ffmpeg -hide_banner -loglevel error -y -i (Join-Path $Outro 'analytics-bridge-clean.mp4') `
        -i (Join-Path $ProjectRoot 'releases\latest\final-analytics-v3-clean.mp4') `
        -filter_complex '[0:v]fps=60,settb=AVTB,setsar=1[a];[1:v]fps=60,settb=AVTB,setsar=1[b];[a][b]xfade=transition=fade:duration=1:offset=4,format=yuv420p[v]' `
        -map '[v]' -an -t 10 -r 60 -c:v libx264 -preset fast -crf 16 -movflags +faststart (Join-Path $Outro 'analytics-outro-clean.mp4')
    Check-Exit 'Outro assembly'
}
$SourceArguments = @()
if ($MainSource) { $SourceArguments += @('--main-source', $MainSource) }
if ($MechanicalSource) { $SourceArguments += @('--mechanical-source', $MechanicalSource) }
& $Python (Join-Path $ProjectRoot 'scripts\finalize_subtitled_films.py') --out $OutputDirectory @SourceArguments
Check-Exit 'Subtitled final films'
Write-Host "Final videos and captions: $OutputDirectory"
