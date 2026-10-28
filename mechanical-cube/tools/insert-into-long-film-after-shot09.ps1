param(
    [string]$MainVideo = 'videos\10月27日.mp4',
    [string]$TransitionVideo = 'mechanical-cube\releases\latest\mechanical-transition-card-voiceover.mp4',
    [string]$MechanicalShot = 'mechanical-cube\releases\latest\c159cc4d19a03485a4677970789f6f1a.mp4',
    [string]$MechanicalVoiceSource = 'mechanical-cube\releases\latest\mechanical-cube-main-ai-integrated-voiceover.mp4',
    [string]$FinalAnalytics = 'mechanical-cube\releases\latest\final-analytics-v2-voiceover.mp4',
    [string]$OutputVideo = 'videos\application-knowledge-graph-with-mechanical-replay.mp4'
)

$ErrorActionPreference = 'Stop'
$RepositoryRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$MainPath = Join-Path $RepositoryRoot $MainVideo
$TransitionPath = Join-Path $RepositoryRoot $TransitionVideo
$ShotPath = Join-Path $RepositoryRoot $MechanicalShot
$VoicePath = Join-Path $RepositoryRoot $MechanicalVoiceSource
$FinalAnalyticsPath = Join-Path $RepositoryRoot $FinalAnalytics
$OutputPath = Join-Path $RepositoryRoot $OutputVideo

foreach ($path in @($MainPath, $TransitionPath, $ShotPath, $VoicePath, $FinalAnalyticsPath)) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Input not found: $path" }
}

$VideoFilter = @(
    '[0:v]trim=start=0:end=62,setpts=PTS-STARTPTS,fps=60[first]'
    '[1:v]setpts=PTS-STARTPTS,fps=60[transition]'
    '[2:v]setpts=PTS-STARTPTS,fps=60[mechanical]'
    '[4:v]setpts=PTS-STARTPTS,fps=60[last]'
    '[first][transition]xfade=transition=fadeblack:duration=0.60:offset=61.40[first_join]'
    '[first_join][mechanical]xfade=transition=fadeblack:duration=0.60:offset=64.80[mechanical_join]'
    '[mechanical_join][last]xfade=transition=fadeblack:duration=0.75:offset=78.05,format=yuv420p[video]'
) -join ';'

$AudioFilter = @(
    '[0:a]atrim=start=0:end=62,asetpts=PTS-STARTPTS[first_audio]'
    '[1:a]atrim=start=0:end=4,asetpts=PTS-STARTPTS[transition_audio]'
    '[3:a]atrim=start=13.25:end=27.25,asetpts=PTS-STARTPTS[mechanical_audio]'
    '[4:a]asetpts=PTS-STARTPTS[last_audio]'
    '[first_audio][transition_audio]acrossfade=d=0.60:c1=tri:c2=tri[first_audio_join]'
    '[first_audio_join][mechanical_audio]acrossfade=d=0.60:c1=tri:c2=tri[mechanical_audio_join]'
    '[mechanical_audio_join][last_audio]acrossfade=d=0.75:c1=tri:c2=tri[audio]'
) -join ';'

ffmpeg -y -i $MainPath -i $TransitionPath -i $ShotPath -i $VoicePath -i $FinalAnalyticsPath `
    -filter_complex "$VideoFilter;$AudioFilter" `
    -map '[video]' -map '[audio]' `
    -r 60 -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p `
    -c:a aac -b:a 192k -ar 48000 -movflags +faststart $OutputPath

if ($LASTEXITCODE -ne 0) { throw 'FFmpeg assembly failed.' }
Write-Host "Complete: $OutputPath"

