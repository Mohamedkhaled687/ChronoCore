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
    --hidden-import PySide6.QtCore `
    --hidden-import PySide6.QtGui `
    --hidden-import PySide6.QtWidgets `
    --exclude-module PySide6.Qt3DAnimation `
    --exclude-module PySide6.Qt3DCore `
    --exclude-module PySide6.Qt3DExtras `
    --exclude-module PySide6.Qt3DInput `
    --exclude-module PySide6.Qt3DLogic `
    --exclude-module PySide6.Qt3DRender `
    --exclude-module PySide6.QtBluetooth `
    --exclude-module PySide6.QtCharts `
    --exclude-module PySide6.QtConcurrent `
    --exclude-module PySide6.QtDataVisualization `
    --exclude-module PySide6.QtDesigner `
    --exclude-module PySide6.QtGraphs `
    --exclude-module PySide6.QtHelp `
    --exclude-module PySide6.QtMultimedia `
    --exclude-module PySide6.QtMultimediaWidgets `
    --exclude-module PySide6.QtNetworkAuth `
    --exclude-module PySide6.QtOpenGL `
    --exclude-module PySide6.QtOpenGLWidgets `
    --exclude-module PySide6.QtPdf `
    --exclude-module PySide6.QtPdfWidgets `
    --exclude-module PySide6.QtPositioning `
    --exclude-module PySide6.QtPrintSupport `
    --exclude-module PySide6.QtQml `
    --exclude-module PySide6.QtQuick `
    --exclude-module PySide6.QtQuick3D `
    --exclude-module PySide6.QtQuickControls2 `
    --exclude-module PySide6.QtQuickWidgets `
    --exclude-module PySide6.QtRemoteObjects `
    --exclude-module PySide6.QtScxml `
    --exclude-module PySide6.QtSensors `
    --exclude-module PySide6.QtSerialBus `
    --exclude-module PySide6.QtSerialPort `
    --exclude-module PySide6.QtSql `
    --exclude-module PySide6.QtStateMachine `
    --exclude-module PySide6.QtSvg `
    --exclude-module PySide6.QtSvgWidgets `
    --exclude-module PySide6.QtTest `
    --exclude-module PySide6.QtTextToSpeech `
    --exclude-module PySide6.QtUiTools `
    --exclude-module PySide6.QtWebChannel `
    --exclude-module PySide6.QtWebEngineCore `
    --exclude-module PySide6.QtWebEngineQuick `
    --exclude-module PySide6.QtWebEngineWidgets `
    --exclude-module PySide6.QtWebSockets `
    --exclude-module PySide6.QtWebView `
    --exclude-module PySide6.QtXml `
    main.py

if (-not (Test-Path "dist\ChronoCore.exe")) {
    throw "Build failed: dist\ChronoCore.exe was not created."
}

Write-Host "Build complete: dist\ChronoCore.exe"
