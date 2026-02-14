"""
View components for PrecipGen Desktop application.

This package contains CustomTkinter-based UI components following
the Model-View-Controller pattern. Each panel represents a distinct
page in the tab-based navigation workflow.
"""

from precipgen.desktop.views.main_window import MainWindow
from precipgen.desktop.views.home_panel import HomePanel
from precipgen.desktop.views.search_panel import SearchPanel
from precipgen.desktop.views.upload_panel import UploadPanel
from precipgen.desktop.views.basic_analysis_panel import BasicAnalysisPanel
from precipgen.desktop.views.markov_analysis_panel import MarkovAnalysisPanel
from precipgen.desktop.views.trend_analysis_panel import TrendAnalysisPanel

__all__ = [
    'MainWindow',
    'HomePanel',
    'SearchPanel',
    'UploadPanel',
    'BasicAnalysisPanel',
    'MarkovAnalysisPanel',
    'TrendAnalysisPanel'
]
