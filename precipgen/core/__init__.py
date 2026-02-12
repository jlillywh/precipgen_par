"""Core analysis modules for precipitation parameter calculation."""

from precipgen.core.time_series import TimeSeries
from precipgen.core.pgpar import calculate_params, calculate_window_params
from precipgen.core.pgpar_ext import calculate_ext_params
from precipgen.core.pgpar_wave import PrecipGenPARWave, analyze_precipgen_parameter_waves
from precipgen.core.random_walk_params import RandomWalkParameterAnalyzer, analyze_random_walk_parameters
from precipgen.core.precip_stats import PrecipValidator
from precipgen.core.long_term_analyzer import LongTermAnalyzer

__all__ = [
    "TimeSeries",
    "calculate_params",
    "calculate_window_params",
    "calculate_ext_params",
    "PrecipGenPARWave",
    "analyze_precipgen_parameter_waves",
    "RandomWalkParameterAnalyzer",
    "analyze_random_walk_parameters",
    "PrecipValidator",
    "LongTermAnalyzer",
]
