#!/usr/bin/env python3
"""
PID Tuning App Launcher
Automatically checks and installs required dependencies before running the app.
"""

import sys
import subprocess
import importlib
import os

def check_and_install_package(package_name, import_name=None):
    """Check if a package is installed, install if not."""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✓ {package_name} is already installed")
        return True
    except ImportError:
        print(f"✗ {package_name} not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"✓ {package_name} installed successfully")
            return True
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package_name}")
            return False

def main():
    print("PID Tuning App - Dependency Checker")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("✗ Python 3.7 or higher is required")
        print(f"  Current version: {sys.version}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # List of required packages
    dependencies = [
        ("pyserial", "serial"),
        ("matplotlib", "matplotlib"),
        ("numpy", "numpy"),
    ]
    
    print("\nChecking dependencies...")
    all_installed = True
    
    for package, import_name in dependencies:
        if not check_and_install_package(package, import_name):
            all_installed = False
    
    if not all_installed:
        print("\n✗ Some dependencies could not be installed")
        input("Press Enter to exit...")
        sys.exit(1)
    
    print("\n✓ All dependencies satisfied!")
    print("\nStarting PID Tuning App...")
    print("-" * 40)
    
    # Run the main application
    try:
        # Import and run the app
        import pid_tuning_app
        pid_tuning_app.main()
    except Exception as e:
        print(f"\n✗ Error running application: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
