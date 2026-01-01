# Building PID Tuning App Executable

## Quick Build (Windows)

1. **Double-click `build.bat`**
   - This will automatically install PyInstaller if needed
   - Build the standalone executable
   - The final EXE will be in the `dist/` folder

## Manual Build

If the batch file doesn't work, run these commands:

```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
pyinstaller --onefile --windowed --name=PID_Tuning_App pid_tuning_app.py
```

## Advanced Build Options

For a smaller executable with an external icon:

```bash
pyinstaller --onefile --windowed --name=PID_Tuning_App --icon=icon.ico pid_tuning_app.py
```

## Distribution

The generated executable (`dist/PID_Tuning_App.exe`):
- ✅ Requires no Python installation
- ✅ Includes all dependencies
- ✅ Works on any Windows 7+ PC
- ✅ Single file - easy to share

## Troubleshooting

**Antivirus Warning**: Some antivirus software may flag the EXE as suspicious. This is a false positive common to PyInstaller apps. You may need to add an exception.

**Large File Size**: The executable is ~50-100MB because it includes Python and all libraries. This is normal.

**Slow Startup**: First launch may be slower as it unpacks dependencies. Subsequent launches are faster.

## Requirements for Building

- Python 3.7 or higher
- All required libraries installed:
  ```bash
  pip install pyserial matplotlib numpy
  ```

## Optional: Create Installer

For professional distribution, consider using Inno Setup to create an installer with:
- Desktop shortcut
- Start menu entry
- Uninstaller
- Proper Windows integration
