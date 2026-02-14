"""
Controllers for PrecipGen Desktop application.

This package contains controller classes that coordinate business logic
between the UI layer and the core/data modules.
"""

from precipgen.desktop.controllers.project_controller import ProjectController
from precipgen.desktop.controllers.data_controller import (
    DataController,
    StationMetadata,
    SearchCriteria,
    Result
)
from precipgen.desktop.controllers.analysis_controller import (
    AnalysisController,
    BasicAnalysisResults,
    MarkovParameters,
    TrendAnalysisResults
)

__all__ = [
    'ProjectController',
    'DataController',
    'StationMetadata',
    'SearchCriteria',
    'Result',
    'AnalysisController',
    'BasicAnalysisResults',
    'MarkovParameters',
    'TrendAnalysisResults'
]
