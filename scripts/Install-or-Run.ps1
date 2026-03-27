$ErrorActionPreference = "Stop"

param(
    [string]$Version = "latest"
)

function Find-InstalledExe {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Verse Switcher\verse-switcher.exe"),
        (Join-Path $PSScriptRoot "..\dist\verse-switcher.exe")
    )
    foreach ($path in $candidates) {
        $resolved = [System.IO.Path]::GetFullPath($path)
        if (Test-Path $resolved) {
            return $resolved
        }
    }
    return $null
}

function Resolve-ReleaseAssetUrl([string]$RequestedVersion) {
    if ($RequestedVersion -eq "latest") {
        return "https://github.com/hugsndnugs/rsi-versioner/releases/latest/download/verse-switcher-setup.exe"
    }
    return "https://github.com/hugsndnugs/rsi-versioner/releases/download/$RequestedVersion/verse-switcher-setup.exe"
}

function Install-FromRelease([string]$RequestedVersion) {
    $tempDir = Join-Path $env:TEMP "verse-switcher-bootstrap"
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    $installerPath = Join-Path $tempDir "verse-switcher-setup.exe"
    $url = Resolve-ReleaseAssetUrl -RequestedVersion $RequestedVersion
    Write-Host "Downloading installer from $url"
    Invoke-WebRequest -Uri $url -OutFile $installerPath
    Write-Host "Running installer..."
    $proc = Start-Process -FilePath $installerPath -ArgumentList "/VERYSILENT","/NORESTART" -PassThru -Wait
    if ($proc.ExitCode -ne 0) {
        throw "Installer failed with exit code $($proc.ExitCode)"
    }
}

$exePath = Find-InstalledExe
if (-not $exePath) {
    Write-Host "Verse Switcher not found. Installing..."
    Install-FromRelease -RequestedVersion $Version
    $exePath = Find-InstalledExe
}

if (-not $exePath) {
    throw "Install completed but verse-switcher.exe was not found."
}

Write-Host "Launching: $exePath"
Start-Process -FilePath $exePath
