# ChronoCore

## Build a Windows EXE

Use one of these options to produce a standalone `ChronoCore.exe`:

- **GitHub Actions (recommended):**
  - Run the `Build Windows EXE` workflow.
  - Download the `ChronoCore-windows-exe` artifact.
  - The artifact includes:
    - `dist/ChronoCore.exe`
    - `dist/ChronoCore-windows.zip`

- **Local Windows machine:**
  - Open PowerShell in the project root.
  - Run:
    - `.\scripts\build_windows_exe.ps1`

The build script uses a slim PyInstaller profile that keeps only the Qt modules used by this app (`QtCore`, `QtGui`, `QtWidgets`) to reduce final artifact size.
