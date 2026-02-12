"""
PrecipGen PAR - Precipitation Parameter Analysis and Generation

A tool for analyzing historical precipitation data and generating parameters
for stochastic precipitation modeling.
"""

__version__ = "1.2.0"
__author__ = "PrecipGen Contributors"

from precipgen.core.time_series import TimeSeries
from precipgen.core.pgpar import calculate_params, calculate_window_params

__all__ = [
    "TimeSeries",
    "calculate_params",
    "calculate_window_params",
]
