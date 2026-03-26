$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

python -m pip install -e ".[build]"

$version = (python -c "from importlib.metadata import version; print(version('rsi-versioner'))").Trim()
$distDir = Join-Path $repoRoot "dist"
$buildDir = Join-Path $repoRoot "build\pyinstaller"

if (Test-Path $buildDir) {
    Remove-Item -Recurse -Force $buildDir
}

if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Path $distDir | Out-Null
}

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name "rsi-versioner" `
  --distpath "$distDir" `
  --workpath "$buildDir" `
  --specpath "$buildDir" `
  "src/rsi_versioner/__main__.py"

Write-Host "Portable build complete: dist/rsi-versioner.exe (version $version)"
