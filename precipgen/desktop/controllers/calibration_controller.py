"""
Calibration controller for parameter adjustment and export.

This module manages interactive parameter calibration including adjustment,
validation, reset operations, and export functionality. It coordinates between
the UI layer and the core analysis modules while maintaining parameter state.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd

from precipgen.desktop.models.app_state import AppState


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AdjustedParameters:
    """
    User-adjusted parameters for stress testing.
    
    Stores monthly parameter values that have been adjusted by the user
    through the calibration interface, along with calculated deviations
    from the historical baseline values.
    
    Attributes:
        alpha: Alpha parameter values (12 monthly values)
        beta: Beta parameter values (12 monthly values)
        p_wet_wet: P(W|W) probability values (12 monthly values)
        p_wet_dry: P(W|D) probability values (12 monthly values)
        p_dry_wet: P(D|W) probability values (12 monthly values)
        p_dry_dry: P(D|D) probability values (12 monthly values)
        deviations: Dictionary mapping parameter names to deviation values
    """
    alpha: pd.DataFrame
    beta: pd.DataFrame
    p_wet_wet: pd.DataFrame
    p_wet_dry: pd.DataFrame
    p_dry_wet: pd.DataFrame
    p_dry_dry: pd.DataFrame
    deviations: Dict[str, pd.DataFrame] = field(default_factory=dict)


@dataclass
class Result:
    """
    Generic result type for operations that can fail.
    
    Attributes:
        success: True if operation succeeded, False otherwise
        value: Result value if successful, None otherwise
        error: Error message if failed, None otherwise
    """
    success: bool
    value: Optional[any] = None
    error: Optional[str] = None


class CalibrationController:
    """
    Manages parameter adjustment and export.
    
    Coordinates interactive parameter calibration including real-time
    adjustment, validation, deviation calculation, reset operations,
    and export functionality. Maintains adjusted parameter state and
    notifies observers of changes.
    
    Attributes:
        app_state: Runtime application state
    """
    
    def __init__(self, app_state: AppState):
        """
        Initialize CalibrationController.
        
        Args:
            app_state: AppState instance for runtime state management
        """
        self.app_state = app_state
    
    def adjust_parameter(
        self,
        param_name: str,
        month: int,
        value: float
    ) -> Result:
        """
        Update adjusted parameter and trigger visualization update.
        
        Adjusts a specific parameter value for a given month, validates
        the new value, calculates deviation from historical baseline,
        and updates the application state to trigger UI updates.
        
        Args:
            param_name: Name of parameter to adjust ('alpha', 'beta', 'p_wet_wet', etc.)
            month: Month index (1-12) for the parameter to adjust
            value: New parameter value
            
        Returns:
            Result object containing:
            - success: True if adjustment succeeded
            - value: Updated AdjustedParameters object if successful
            - error: Error message if failed
        """
        try:
            # Validate that historical parameters exist
            if not self.app_state.has_historical_params():
                return Result(
                    success=False,
                    error="No historical parameters available. Please calculate parameters first."
                )
            
            # Validate month range
            if month < 1 or month > 12:
                return Result(
                    success=False,
                    error=f"Invalid month: {month}. Must be between 1 and 12."
                )
            
            # Validate parameter name
            valid_params = ['alpha', 'beta', 'p_wet_wet', 'p_wet_dry', 'p_dry_wet', 'p_dry_dry']
            if param_name not in valid_params:
                return Result(
                    success=False,
                    error=f"Invalid parameter name: {param_name}. Must be one of {valid_params}"
                )
            
            # Validate parameter value (Requirements 5.5)
            is_valid, error_msg = self.validate_parameter(param_name, value)
            if not is_valid:
                return Result(
                    success=False,
                    error=error_msg
                )
            
            # Get or create adjusted parameters
            adjusted_params = self._get_or_create_adjusted_params()
            
            # Update the specific parameter value
            param_attr = self._get_param_attribute_name(param_name)
            param_df = getattr(adjusted_params, param_attr)
            
            # Update the value for the specified month (month is 1-indexed, DataFrame is 0-indexed)
            param_df.iloc[month - 1] = value
            
            # Recalculate deviations (Requirements 5.3)
            self._calculate_deviations(adjusted_params)
            
            # Update app state to trigger observers
            self.app_state.set_adjusted_params(adjusted_params)
            
            logger.info(f"Adjusted {param_name} for month {month} to {value}")
            
            return Result(
                success=True,
                value=adjusted_params,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error adjusting parameter {param_name}: {e}", exc_info=True)
            return Result(
                success=False,
                error=f"Parameter Adjustment Error\n\n"
                      f"Failed to adjust parameter: {param_name}\n\n"
                      f"Details: {str(e)}\n\n"
                      f"Please check the log file for more information."
            )
    
    def reset_to_historical(self) -> Result:
        """
        Reset all parameters to historical values.
        
        Restores all adjusted parameters to their original historical
        baseline values and clears all deviations. Updates application
        state to trigger UI refresh.
        
        Returns:
            Result object containing:
            - success: True if reset succeeded
            - value: Reset AdjustedParameters object if successful
            - error: Error message if failed
        """
        try:
            # Validate that historical parameters exist
            if not self.app_state.has_historical_params():
                return Result(
                    success=False,
                    error="No historical parameters available. Cannot reset."
                )
            
            # Create new adjusted parameters from historical values
            historical = self.app_state.historical_params
            
            adjusted_params = AdjustedParameters(
                alpha=historical.alpha.copy(),
                beta=historical.beta.copy(),
                p_wet_wet=historical.p_wet_wet.copy(),
                p_wet_dry=historical.p_wet_dry.copy(),
                p_dry_wet=historical.p_dry_wet.copy(),
                p_dry_dry=historical.p_dry_dry.copy(),
                deviations={}
            )
            
            # Calculate deviations (should all be zero)
            self._calculate_deviations(adjusted_params)
            
            # Update app state
            self.app_state.set_adjusted_params(adjusted_params)
            
            logger.info("Reset all parameters to historical values")
            
            return Result(
                success=True,
                value=adjusted_params,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error resetting parameters: {e}", exc_info=True)
            return Result(
                success=False,
                error=f"Parameter Reset Error\n\n"
                      f"Failed to reset parameters to historical values.\n\n"
                      f"Details: {str(e)}\n\n"
                      f"Please check the log file for more information."
            )
    
    def validate_parameter(
        self,
        param_name: str,
        value: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if parameter value is physically valid.
        
        Validates that parameter values fall within physically reasonable
        ranges based on the parameter type:
        - Alpha: > 0 (typically 0.1 - 5.0)
        - Beta: > 0 (typically 0.1 - 5.0)
        - Probabilities: 0.0 - 1.0
        
        Args:
            param_name: Name of parameter to validate
            value: Parameter value to check
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if value is valid, False otherwise
            - error_message: Description of validation failure, None if valid
        """
        # Validate alpha and beta parameters
        if param_name in ['alpha', 'beta']:
            if value <= 0:
                return False, f"{param_name} must be greater than 0"
            if value > 10.0:
                return False, f"{param_name} value {value} is unreasonably large (typical range: 0.1-5.0)"
            # Warning for values outside typical range (but still allow them)
            if value < 0.1 or value > 5.0:
                logger.warning(f"{param_name} value {value} is outside typical range (0.1-5.0)")
        
        # Validate probability parameters
        elif param_name in ['p_wet_wet', 'p_wet_dry', 'p_dry_wet', 'p_dry_dry']:
            if value < 0.0 or value > 1.0:
                return False, f"{param_name} must be between 0.0 and 1.0"
        
        else:
            return False, f"Unknown parameter: {param_name}"
        
        return True, None
    
    def export_parameters(self, output_path: Optional[Path] = None) -> Result:
        """
        Write finalized parameters using precipgen.core exporter.
        
        Exports the current adjusted parameters (or historical if no adjustments)
        to a file in the project folder. Includes metadata such as timestamp,
        source station, and date range.
        
        Args:
            output_path: Optional custom output path. If None, uses project folder.
            
        Returns:
            Result object containing:
            - success: True if export succeeded
            - value: Path to exported file if successful
            - error: Error message if failed
        """
        try:
            # Check if project folder is set
            if not self.app_state.has_project_folder():
                return Result(
                    success=False,
                    error="No project folder selected. Please select a project folder first."
                )
            
            # Check if parameters exist
            if not self.app_state.has_historical_params():
                return Result(
                    success=False,
                    error="No parameters available to export. Please calculate parameters first."
                )
            
            # Determine which parameters to export
            params_to_export = self.app_state.adjusted_params if self.app_state.has_adjusted_params() else self.app_state.historical_params
            
            # Determine output path
            if output_path is None:
                exports_dir = self.app_state.project_folder / 'exports'
                exports_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                station_id = self.app_state.historical_params.source_station
                output_path = exports_dir / f"{station_id}_params_{timestamp}.csv"
            
            # Check if output directory is writable
            output_dir = output_path.parent
            if not output_dir.exists():
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    return Result(
                        success=False,
                        error=f"Cannot create output directory: {output_dir}. Permission denied."
                    )
            
            # Combine all parameters into a single DataFrame
            params_df = self._create_export_dataframe(params_to_export)
            
            # Write to CSV
            params_df.to_csv(output_path)
            
            # Write metadata file
            metadata_path = output_path.with_suffix('.txt')
            self._write_metadata_file(metadata_path, params_to_export)
            
            logger.info(f"Parameters exported to {output_path}")
            
            return Result(
                success=True,
                value=output_path,
                error=None
            )
            
        except PermissionError as e:
            logger.error(f"Permission error during export: {e}", exc_info=True)
            return Result(
                success=False,
                error=f"Permission Denied\n\n"
                      f"Cannot write to output location:\n{output_path}\n\n"
                      f"Details: {str(e)}\n\n"
                      f"Suggestions:\n"
                      f"• Check folder permissions\n"
                      f"• Ensure the folder is not read-only\n"
                      f"• Close any programs that may have the file open\n"
                      f"• Try selecting a different project folder"
            )
        except Exception as e:
            logger.error(f"Error exporting parameters: {e}", exc_info=True)
            return Result(
                success=False,
                error=f"Export Error\n\n"
                      f"Failed to export parameters to file.\n\n"
                      f"Details: {str(e)}\n\n"
                      f"Please check the log file for more information."
            )
    
    def _get_or_create_adjusted_params(self) -> AdjustedParameters:
        """
        Get existing adjusted parameters or create from historical.
        
        Returns:
            AdjustedParameters object
        """
        if self.app_state.has_adjusted_params():
            return self.app_state.adjusted_params
        
        # Create new adjusted parameters from historical
        historical = self.app_state.historical_params
        
        adjusted_params = AdjustedParameters(
            alpha=historical.alpha.copy(),
            beta=historical.beta.copy(),
            p_wet_wet=historical.p_wet_wet.copy(),
            p_wet_dry=historical.p_wet_dry.copy(),
            p_dry_wet=historical.p_dry_wet.copy(),
            p_dry_dry=historical.p_dry_dry.copy(),
            deviations={}
        )
        
        # Calculate initial deviations (should all be zero)
        self._calculate_deviations(adjusted_params)
        
        return adjusted_params
    
    def _calculate_deviations(self, adjusted_params: AdjustedParameters) -> None:
        """
        Calculate deviations from historical parameters.
        
        Updates the deviations dictionary in the AdjustedParameters object
        with the difference between adjusted and historical values for each
        parameter.
        
        Args:
            adjusted_params: AdjustedParameters object to update
        """
        historical = self.app_state.historical_params
        
        # Calculate deviation for each parameter
        adjusted_params.deviations = {
            'alpha': adjusted_params.alpha - historical.alpha,
            'beta': adjusted_params.beta - historical.beta,
            'p_wet_wet': adjusted_params.p_wet_wet - historical.p_wet_wet,
            'p_wet_dry': adjusted_params.p_wet_dry - historical.p_wet_dry,
            'p_dry_wet': adjusted_params.p_dry_wet - historical.p_dry_wet,
            'p_dry_dry': adjusted_params.p_dry_dry - historical.p_dry_dry,
        }
    
    def _get_param_attribute_name(self, param_name: str) -> str:
        """
        Convert parameter name to attribute name.
        
        Args:
            param_name: Parameter name (e.g., 'alpha', 'p_wet_wet')
            
        Returns:
            Attribute name for AdjustedParameters object
        """
        return param_name
    
    def _create_export_dataframe(self, params) -> pd.DataFrame:
        """
        Create a combined DataFrame for export.
        
        Args:
            params: HistoricalParameters or AdjustedParameters object
            
        Returns:
            DataFrame with all parameters
        """
        # Combine all parameters into a single DataFrame
        export_df = pd.DataFrame({
            'ALPHA': params.alpha.iloc[:, 0],
            'BETA': params.beta.iloc[:, 0],
            'PWW': params.p_wet_wet.iloc[:, 0],
            'PWD': params.p_wet_dry.iloc[:, 0],
            'PDW': params.p_dry_wet.iloc[:, 0],
            'PDD': params.p_dry_dry.iloc[:, 0],
        })
        
        # Set month as index (1-12)
        export_df.index = range(1, 13)
        export_df.index.name = 'MONTH'
        
        return export_df
    
    def _write_metadata_file(self, metadata_path: Path, params) -> None:
        """
        Write metadata file with parameter information.
        
        Args:
            metadata_path: Path to metadata file
            params: HistoricalParameters or AdjustedParameters object
        """
        try:
            # Get historical params for metadata
            historical = self.app_state.historical_params
            
            with open(metadata_path, 'w') as f:
                f.write("PrecipGen Parameter Export\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Export Date: {datetime.now().isoformat()}\n")
                f.write(f"Source Station: {historical.source_station}\n")
                f.write(f"Data Range: {historical.date_range[0]} to {historical.date_range[1]}\n")
                f.write(f"Calculation Date: {historical.calculation_date.isoformat()}\n\n")
                
                # Indicate if parameters were adjusted
                if self.app_state.has_adjusted_params():
                    f.write("Parameters: User-Adjusted (Calibrated)\n")
                else:
                    f.write("Parameters: Historical (Baseline)\n")
                
                f.write("\n" + "=" * 50 + "\n")
            
            logger.info(f"Metadata written to {metadata_path}")
            
        except Exception as e:
            logger.warning(f"Failed to write metadata file: {e}")
