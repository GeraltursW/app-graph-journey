param(
    [string]$BlenderExe = $env:BLENDER_EXE,
    [switch]$SkipBlender,
    [switch]$SkipVoiceover
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$IntroOut = Join-Path $ProjectRoot 'output\robot-arm\cube-xray-intro'
$AiOut = Join-Path $ProjectRoot 'output\robot-arm\cube-ai-control-loop'
$IntroFrames = Join-Path $IntroOut 'frames'
$AiFrames = Join-Path $AiOut 'frames'

if (-not $BlenderExe) {
    $blenderCommand = Get-Command blender -ErrorAction SilentlyContinue
    if ($blenderCommand) { $BlenderExe = $blenderCommand.Source }
}

if (-not $SkipBlender) {
    if (-not $BlenderExe -or -not (Test-Path -LiteralPath $BlenderExe)) {
        throw 'Blender was not found. Pass -BlenderExe or set BLENDER_EXE.'
    }
    & $BlenderExe --background --python (Join-Path $ProjectRoot 'scripts\render_robot_cube_xray_intro.py')
    & $BlenderExe --background --python (Join-Path $ProjectRoot 'scripts\render_robot_cube_ai_control_loop.py')
}

$IntroPattern = Join-Path $IntroFrames 'frame_%04d.png'
$AiPattern = Join-Path $AiFrames 'frame_%04d.png'
if (-not (Test-Path -LiteralPath (Join-Path $IntroFrames 'frame_0001.png'))) { throw 'The X-ray frame sequence is missing.' }
if (-not (Test-Path -LiteralPath (Join-Path $AiFrames 'frame_0001.png'))) { throw 'The AI-loop frame sequence is missing.' }

$IntroVideo = Join-Path $IntroOut 'mechanical_cube_xray_intro_preview.mp4'
$AiVideo = Join-Path $AiOut 'mechanical_cube_ai_control_loop.mp4'
$AiSlow = Join-Path $AiOut 'mechanical_cube_ai_control_loop_12s_smooth.mp4'
$CleanVideo = Join-Path $AiOut 'mechanical_cube_intro_plus_ai_loop_smooth.mp4'

ffmpeg -y -framerate 24 -start_number 1 -i $IntroPattern -c:v libx264 -crf 17 -pix_fmt yuv420p -movflags +faststart $IntroVideo
ffmpeg -y -framerate 24 -start_number 1 -i $AiPattern -c:v libx264 -crf 17 -pix_fmt yuv420p -movflags +faststart $AiVideo
ffmpeg -y -i $AiVideo -vf 'setpts=1.5*PTS' -an -r 24 -c:v libx264 -crf 17 -pix_fmt yuv420p -movflags +faststart $AiSlow
ffmpeg -y -i $IntroVideo -i $AiSlow -filter_complex '[0:v][1:v]xfade=transition=fade:duration=1:offset=14,format=yuv420p[v]' -map '[v]' -r 24 -c:v libx264 -crf 17 -movflags +faststart $CleanVideo

if (-not $SkipVoiceover) {
    $VenvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $VenvPython)) { throw 'Missing .venv. Run tools\setup.ps1 first.' }
    & $VenvPython (Join-Path $ProjectRoot 'scripts\generate_mechanical_cube_voiceover.py')
}

Write-Host "Complete: $CleanVideo"

