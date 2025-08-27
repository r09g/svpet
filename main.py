#!/usr/bin/env python3

import sys
import signal
from PySide6.QtWidgets import QApplication
from src.desktop_pet import DesktopPetApp

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\nExiting application...")
    QApplication.quit()

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running even when windows are closed
    
    pet_app = DesktopPetApp()
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    main()