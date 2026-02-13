"""
PrecipGen Desktop Application Package.

This package contains the CustomTkinter-based Windows desktop application
for precipitation parameter calibration.
"""

from precipgen.desktop.app import DesktopApp
from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.models.session_config import SessionConfig
from precipgen.desktop.views.main_window import MainWindow

__version__ = "1.0.0"

__all__ = ['DesktopApp', 'AppState', 'SessionConfig', 'MainWindow']
