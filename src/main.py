#!/usr/bin/env python3

import sys
import signal
import argparse
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from desktop_pet import DesktopPetApp
from config import set_debug_mode

# Prevent direct execution of this file
if __name__ == "__main__" and os.path.basename(os.path.dirname(os.path.abspath(__file__))) == "src":
    print("Error: This script should not be run directly.")
    print("Please use the main.py file in the project root directory instead.")
    print("Usage: python main.py")
    sys.exit(1)

# Global reference to pet app for signal handler
pet_app_instance = None

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\nExiting application...")
    global pet_app_instance
    if pet_app_instance:
        pet_app_instance.quit_application()
    else:
        app = QApplication.instance()
        if app:
            app.quit()
        sys.exit(0)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Desktop Pet Application')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode')
    return parser.parse_args()

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    args = parse_args()
    
    app = QApplication(sys.argv)
    
    # Set up a timer to allow Ctrl+C to work properly in Qt
    timer = QTimer()
    timer.timeout.connect(lambda: None)  # No-op, just lets Qt process signals
    timer.start(100)  # Check every 100ms
    
    # Set debug mode
    if args.debug:
        set_debug_mode(True)
        print("Debug mode enabled - terminal logging active")
    else:
        set_debug_mode(False)
    
    # Normal desktop pet mode
    app.setQuitOnLastWindowClosed(False)  # Keep running even when windows are closed
    global pet_app_instance
    pet_app_instance = DesktopPetApp()
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    main()