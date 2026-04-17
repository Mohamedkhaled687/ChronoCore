$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

$PythonExe = ".venv\Scripts\python.exe"
$PyInstallerExe = ".venv\Scripts\pyinstaller.exe"

& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r requirements.txt pyinstaller

& $PyInstallerExe `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "ChronoCore" `
    --collect-all PySide6 `
    main.py

if (-not (Test-Path "dist\ChronoCore.exe")) {
    throw "Build failed: dist\ChronoCore.exe was not created."
}

Compress-Archive -Path "dist\ChronoCore.exe" -DestinationPath "dist\ChronoCore-windows.zip" -Force
Write-Host "Build complete: dist\ChronoCore.exe and dist\ChronoCore-windows.zip"
