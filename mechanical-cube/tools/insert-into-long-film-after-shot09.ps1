param(
    [string]$MainVideo = 'videos\10月27日.mp4',
    [string]$MechanicalShot = 'mechanical-cube\releases\latest\c159cc4d19a03485a4677970789f6f1a.mp4',
    [string]$MechanicalVoiceSource = 'mechanical-cube\releases\latest\mechanical-cube-main-ai-integrated-voiceover.mp4',
    [string]$OutputVideo = 'videos\application-knowledge-graph-with-mechanical-replay.mp4'
)

$ErrorActionPreference = 'Stop'
$RepositoryRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$MainPath = Join-Path $RepositoryRoot $MainVideo
$ShotPath = Join-Path $RepositoryRoot $MechanicalShot
$VoicePath = Join-Path $RepositoryRoot $MechanicalVoiceSource
$OutputPath = Join-Path $RepositoryRoot $OutputVideo

foreach ($path in @($MainPath, $ShotPath, $VoicePath)) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Input not found: $path" }
}

$VideoFilter = @(
    '[0:v]trim=start=0:end=62,setpts=PTS-STARTPTS,fps=60[first]'
    '[1:v]setpts=PTS-STARTPTS,fps=60[mechanical]'
    '[0:v]trim=start=62:end=67.756009,setpts=PTS-STARTPTS,fps=60[last]'
    '[first][mechanical]xfade=transition=fadeblack:duration=0.75:offset=61.25[first_join]'
    '[first_join][last]xfade=transition=fadeblack:duration=0.75:offset=74.50,format=yuv420p[video]'
) -join ';'

$AudioFilter = @(
    '[0:a]atrim=start=0:end=62,asetpts=PTS-STARTPTS[first_audio]'
    '[2:a]atrim=start=13.25:end=27.25,asetpts=PTS-STARTPTS[mechanical_audio]'
    '[0:a]atrim=start=62:end=67.756009,asetpts=PTS-STARTPTS[last_audio]'
    '[first_audio][mechanical_audio]acrossfade=d=0.75:c1=tri:c2=tri[first_audio_join]'
    '[first_audio_join][last_audio]acrossfade=d=0.75:c1=tri:c2=tri[audio]'
) -join ';'

ffmpeg -y -i $MainPath -i $ShotPath -i $VoicePath `
    -filter_complex "$VideoFilter;$AudioFilter" `
    -map '[video]' -map '[audio]' `
    -r 60 -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p `
    -c:a aac -b:a 192k -ar 48000 -movflags +faststart $OutputPath

if ($LASTEXITCODE -ne 0) { throw 'FFmpeg assembly failed.' }
Write-Host "Complete: $OutputPath"

