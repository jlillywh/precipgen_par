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
from precipgen.desktop.controllers.calibration_controller import (
    CalibrationController,
    AdjustedParameters
)

__all__ = [
    'ProjectController',
    'DataController',
    'StationMetadata',
    'SearchCriteria',
    'Result',
    'CalibrationController',
    'AdjustedParameters'
]
