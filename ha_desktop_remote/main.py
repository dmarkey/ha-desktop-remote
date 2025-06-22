#!/usr/bin/env python3
"""
Home Assistant Desktop Remote Control

Main entry point for the Home Assistant Desktop Remote Control application.
A desktop application for controlling Home Assistant media players and other devices.
"""

import sys
import signal
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon

from .remote_window import RemoteWindow
from . import __version__


def main():
    """Main entry point for the application"""
    # Allow Ctrl+C to close the application
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setApplicationName("Home Assistant Desktop Remote Control")
    app.setApplicationDisplayName("Home Assistant Desktop Remote Control")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("David Markey")
    app.setOrganizationDomain("dmarkey.com")
    
    # Set application icon if available
    try:
        # Try to find the logo in various locations
        possible_icon_paths = [
            Path(__file__).parent.parent / "images" / "logo.png",
            Path("images") / "logo.png",
            Path("logo.png")
        ]
        
        for icon_path in possible_icon_paths:
            if icon_path.exists():
                app.setWindowIcon(QIcon(str(icon_path)))
                break
    except Exception:
        pass  # Continue without icon if not found
    
    # Enable automatic detection of system theme changes
    app.setStyle('Fusion')  # Use Fusion style which respects system themes better
    
    # Set application to follow system color scheme
    app.setStyleSheet("")  # Clear any default styling to use system theme

    # Create a QTimer to periodically process Python signals
    # This is crucial for Ctrl+C to work in a Qt application
    timer = QTimer()
    timer.start(500) # Check every 500ms
    timer.timeout.connect(lambda: None) # Dummy function to keep the event loop alive

    window = RemoteWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())