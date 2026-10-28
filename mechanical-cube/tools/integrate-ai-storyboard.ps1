param(
    [string]$Storyboard = 'releases\latest\c159cc4d19a03485a4677970789f6f1a.mp4',
    [switch]$SkipVoiceover
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Latest = Join-Path $ProjectRoot 'releases\latest'
$StoryboardPath = Join-Path $ProjectRoot $Storyboard
$BaseClean = Join-Path $Latest 'mechanical-cube-ai-control-clean.mp4'
$OutputClean = Join-Path $Latest 'mechanical-cube-main-ai-integrated-clean.mp4'
$OutputVoiced = Join-Path $Latest 'mechanical-cube-main-ai-integrated-voiceover.mp4'
$VoiceOutput = Join-Path $ProjectRoot 'output\robot-arm\cube-ai-control-loop\mechanical_cube_integrated_voiceover.wav'
$VoiceParts = Join-Path $ProjectRoot 'output\robot-arm\cube-ai-control-loop\integrated_voiceover_parts'
$VoiceReport = Join-Path $ProjectRoot 'output\robot-arm\cube-ai-control-loop\mechanical_cube_integrated_voiceover_report.json'
$VoiceConfig = Join-Path $ProjectRoot 'config\mechanical_cube_integrated_voiceover.json'

if (-not (Test-Path -LiteralPath $StoryboardPath)) { throw "Storyboard not found: $StoryboardPath" }
if (-not (Test-Path -LiteralPath $BaseClean)) { throw "Base video not found: $BaseClean" }

$VideoFilter = '[0:v]trim=start=0:end=14,setpts=PTS-STARTPTS[first];[1:v]setpts=PTS-STARTPTS[second];[first][second]xfade=transition=fadeblack:duration=0.75:offset=13.25,format=yuv420p[v]'
ffmpeg -y -i $BaseClean -i $StoryboardPath -filter_complex $VideoFilter -map '[v]' -an -r 24 -c:v libx264 -preset slow -crf 17 -movflags +faststart $OutputClean

if (-not $SkipVoiceover) {
    $VenvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $VenvPython)) { $VenvPython = (Get-Command python).Source }
    & $VenvPython (Join-Path $ProjectRoot 'scripts\generate_mechanical_cube_voiceover.py') `
        --config $VoiceConfig `
        --source-video $OutputClean `
        --output-video $OutputVoiced `
        --voice-track $VoiceOutput `
        --report $VoiceReport `
        --parts $VoiceParts
}

Write-Host "Complete: $OutputClean"
if (-not $SkipVoiceover) { Write-Host "Complete: $OutputVoiced" }

