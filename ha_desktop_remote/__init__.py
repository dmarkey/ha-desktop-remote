"""
Home Assistant Desktop Remote Control

A desktop application for controlling Home Assistant media players and other devices
through an intuitive remote control interface.
"""

__version__ = "1.0.4"
__author__ = "David Markey"
__email__ = "david@dmarkey.com"
__description__ = "Desktop remote control application for Home Assistant"

from .remote_manager import RemoteManager
from .remote_window import RemoteWindow
from .remote_wizard import RemoteWizard

__all__ = ["RemoteManager", "RemoteWindow", "RemoteWizard"]
