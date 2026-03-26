$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$portableExe = Join-Path $repoRoot "dist\rsi-versioner.exe"
if (-not (Test-Path $portableExe)) {
    throw "Portable executable not found at $portableExe. Run scripts/build_portable.ps1 first."
}

$version = (python -c "from importlib.metadata import version; print(version('rsi-versioner'))").Trim()
$outputDir = Join-Path $repoRoot "dist"
$issScript = Join-Path $repoRoot "packaging\rsi-versioner.iss"

$iscc = Get-Command "iscc.exe" -ErrorAction SilentlyContinue
if (-not $iscc) {
    throw "Inno Setup Compiler (iscc.exe) is required and not on PATH."
}

$env:RSI_VERSION = $version
$env:RSI_OUTPUT_DIR = $outputDir
$env:RSI_PORTABLE_EXE = $portableExe

& $iscc.Path $issScript

Write-Host "Installer build complete in dist/ (version $version)"
