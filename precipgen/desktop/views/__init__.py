"""
View components for PrecipGen Desktop application.

This package contains CustomTkinter-based UI components following
the Model-View-Controller pattern.
"""

from precipgen.desktop.views.main_window import MainWindow
from precipgen.desktop.views.project_panel import ProjectPanel
from precipgen.desktop.views.data_panel import DataPanel

__all__ = ['MainWindow', 'ProjectPanel', 'DataPanel']
