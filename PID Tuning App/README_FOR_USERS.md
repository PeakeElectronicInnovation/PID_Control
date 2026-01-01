# PID Tuning App - Installation Guide

## Option 1: Standalone Executable (Easiest)

1. Download `PID_Tuning_App.exe`
2. Double-click to run
3. No installation required!

## Option 2: Python Installation (Advanced)

### Prerequisites
- Python 3.7 or higher
- Internet connection for one-time dependency installation

### Quick Start (Windows)

1. **Double-click `Run_PID_App.bat`**
   - This will automatically check and install any missing dependencies
   - The app will start after dependencies are installed

### Manual Installation

If the batch file doesn't work:

1. **Install Python** from https://python.org (if not already installed)

2. **Open Command Prompt** in the app folder and run:
   ```bash
   python run_pid_tuning_app.py
   ```

### Install Dependencies Manually

If automatic installation fails:

```bash
pip install -r requirements.txt
python pid_tuning_app.py
```

### Dependencies

The app requires these Python packages:
- pyserial (for Arduino communication)
- matplotlib (for plotting)
- numpy (for data handling)

### Troubleshooting

**"python is not recognized"**
- Python is not installed or not in your PATH
- Install Python from python.org and make sure to check "Add Python to PATH"

**Permission errors**
- Try running as administrator
- Or use `pip install --user -r requirements.txt`

**Network errors**
- Check your internet connection
- Some corporate networks may block pip - contact your IT department

**Virtual environments (optional)**
For advanced users who want to keep dependencies isolated:
```bash
python -m venv pid_tuning_env
pid_tuning_env\Scripts\activate
pip install -r requirements.txt
python pid_tuning_app.py
```

## Getting Connected

1. Connect your Arduino via USB
2. Open the app
3. Select the correct COM port
4. Click "Connect"
5. Start tuning!

## Need Help?

- Check the "Tuning Guide" tab in the app for detailed instructions
- Make sure your Arduino is running the companion sketch
- Ensure the baud rate is set to 115200
