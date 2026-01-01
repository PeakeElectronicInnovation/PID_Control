#!/usr/bin/env python3
"""
Simple build script for PID Tuning App
"""

import subprocess
import sys
import os

def main():
    print("Installing PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    print("\nBuilding executable...")
    subprocess.check_call([
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=PID_Tuning_App",
        "pid_tuning_app.py"
    ])
    
    print("\n✓ Build complete!")
    print(f"Executable: dist/PID_Tuning_App.exe")

if __name__ == "__main__":
    main()
