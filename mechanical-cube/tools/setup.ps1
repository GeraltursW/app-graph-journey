param(
    [string]$BlenderExe = $env:BLENDER_EXE,
    [switch]$SkipPythonPackages
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot

function Require-Command([string]$Name) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) { throw "Missing command: $Name. Install it and add it to PATH." }
    Write-Host "[OK] $Name -> $($command.Source)"
}

Require-Command git
Require-Command python
Require-Command ffmpeg
Require-Command ffprobe

if (-not $BlenderExe) {
    $blenderCommand = Get-Command blender -ErrorAction SilentlyContinue
    if ($blenderCommand) { $BlenderExe = $blenderCommand.Source }
}
if (-not $BlenderExe -or -not (Test-Path -LiteralPath $BlenderExe)) {
    Write-Warning 'Blender was not found. Pass -BlenderExe or set BLENDER_EXE before rendering.'
} else {
    Write-Host "[OK] Blender -> $BlenderExe"
}

if (-not $SkipPythonPackages) {
    $Venv = Join-Path $ProjectRoot '.venv'
    if (-not (Test-Path -LiteralPath $Venv)) {
        python -m venv $Venv
    }
    $VenvPython = Join-Path $Venv 'Scripts\python.exe'
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r (Join-Path $ProjectRoot 'requirements.txt')
    Write-Host "[OK] Python virtual environment -> $Venv"
}

Write-Host 'Environment check complete. Next: tools\render-latest.ps1.'

