"""
Data controller for GHCN data search, download, and analysis.

This module coordinates GHCN database interactions including station search,
data download with temporary file handling, and integration with the core
analysis modules for parameter calculation.
"""

import tempfile
import shutil
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date
import pandas as pd
import requests

from precipgen.desktop.models.app_state import AppState
from precipgen.data.ghcn_data import GHCNData
from precipgen.data.find_stations import (
    fetch_ghcn_inventory,
    parse_ghcn_inventory
)
from precipgen.core import calculate_params


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class StationMetadata:
    """
    GHCN station information.
    
    Attributes:
        station_id: Unique GHCN station identifier
        name: Human-readable station name
        latitude: Station latitude in degrees
        longitude: Station longitude in degrees
        elevation: Station elevation (if available)
        start_date: First year of data availability
        end_date: Last year of data availability
        data_coverage: Percentage of days with data (0-100)
    """
    station_id: str
    name: str
    latitude: float
    longitude: float
    elevation: Optional[float]
    start_date: int
    end_date: int
    data_coverage: float


@dataclass
class HistoricalParameters:
    """
    Parameters calculated from historical data.
    
    Attributes:
        alpha: Alpha parameter for gamma distribution (monthly values)
        beta: Beta parameter for gamma distribution (monthly values)
        p_wet_wet: Probability of wet day following wet day (monthly values)
        p_wet_dry: Probability of wet day following dry day (monthly values)
        p_dry_wet: Probability of dry day following wet day (monthly values)
        p_dry_dry: Probability of dry day following dry day (monthly values)
        calculation_date: Timestamp when parameters were calculated
        source_station: Station ID used for calculation
        date_range: Tuple of (start_date, end_date) for data used
    """
    alpha: pd.DataFrame  # Monthly alpha values (12 rows)
    beta: pd.DataFrame  # Monthly beta values (12 rows)
    p_wet_wet: pd.DataFrame  # Monthly P(W|W) values (12 rows)
    p_wet_dry: pd.DataFrame  # Monthly P(W|D) values (12 rows)
    p_dry_wet: pd.DataFrame  # Monthly P(D|W) values (12 rows)
    p_dry_dry: pd.DataFrame  # Monthly P(D|D) values (12 rows)
    calculation_date: datetime
    source_station: str
    date_range: Tuple[date, date]


@dataclass
class SearchCriteria:
    """
    Parameters for GHCN station search.
    
    Attributes:
        latitude: Center latitude for radius search (optional)
        longitude: Center longitude for radius search (optional)
        radius_km: Search radius in kilometers (optional)
        state: State code filter (optional)
        start_year: Minimum start year for data
        end_year: Minimum end year for data
        min_coverage: Minimum data coverage percentage (0-100)
    """
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None
    state: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    min_coverage: float = 80.0


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


class DataController:
    """
    Coordinates GHCN data search, download, and analysis.
    
    Handles all interactions with the GHCN database including station search,
    data download with temporary file handling, cleanup operations, and
    integration with core analysis modules.
    
    Attributes:
        app_state: Runtime application state
        temp_download_path: Temporary directory for downloads
    """
    
    def __init__(self, app_state: AppState):
        """
        Initialize DataController.
        
        Args:
            app_state: AppState instance for runtime state management
        """
        self.app_state = app_state
        self.temp_download_path = Path(tempfile.gettempdir()) / "precipgen_downloads"
        
        # Ensure temp directory exists
        self.temp_download_path.mkdir(parents=True, exist_ok=True)
    
    def search_stations(self, criteria: SearchCriteria) -> Result:
        """
        Query GHCN database using precipgen.data module.
        
        Searches for stations matching the provided criteria. Uses the
        existing precipgen.data module functions to fetch and parse
        the GHCN inventory.
        
        Args:
            criteria: SearchCriteria object with search parameters
            
        Returns:
            Result object containing:
            - success: True if search completed
            - value: List of StationMetadata objects if successful
            - error: Error message if failed
        """
        try:
            logger.info("Fetching GHCN inventory...")
            
            # Fetch inventory from GHCN database
            raw_inventory = fetch_ghcn_inventory()
            if raw_inventory is None:
                return Result(
                    success=False,
                    error="Failed to fetch GHCN inventory. Please check your internet connection."
                )
            
            # Parse inventory data
            inventory_df = parse_ghcn_inventory(raw_inventory)
            if inventory_df is None:
                return Result(
                    success=False,
                    error="Failed to parse GHCN inventory data."
                )
            
            logger.info(f"Inventory loaded: {len(inventory_df)} records")
            
            # Filter by element type (PRCP only for now)
            inventory_df = inventory_df[inventory_df['ELEMENT'] == 'PRCP']
            
            # Apply search criteria filters
            filtered_df = self._apply_search_filters(inventory_df, criteria)
            
            if filtered_df.empty:
                return Result(
                    success=True,
                    value=[],
                    error=None
                )
            
            # Group by station and aggregate metadata
            stations = self._aggregate_station_metadata(filtered_df)
            
            logger.info(f"Found {len(stations)} matching stations")
            
            return Result(
                success=True,
                value=stations,
                error=None
            )
            
        except requests.RequestException as e:
            logger.error(f"Network error during station search: {e}", exc_info=True)
            return Result(
                success=False,
                error=f"Network Error\n\n"
                      f"Unable to connect to the NOAA GHCN database.\n\n"
                      f"Details: {str(e)}\n\n"
                      f"Suggestions:\n"
                      f"• Check your internet connection\n"
                      f"• Verify firewall settings allow HTTPS connections\n"
                      f"• Try again in a few moments"
            )
        except Exception as e:
            logger.error(f"Unexpected error during station search: {e}", exc_info=True)
            return Result(
                success=False,
                error=f"Unexpected Error\n\n"
                      f"An error occurred while searching for stations.\n\n"
                      f"Details: {str(e)}\n\n"
                      f"Please check the log file for more information."
            )
    
    def _apply_search_filters(
        self,
        df: pd.DataFrame,
        criteria: SearchCriteria
    ) -> pd.DataFrame:
        """
        Apply search criteria filters to inventory dataframe.
        
        Args:
            df: Inventory dataframe
            criteria: Search criteria
            
        Returns:
            Filtered dataframe
        """
        filtered = df.copy()
        
        # Filter by geographic location (radius search)
        if criteria.latitude is not None and criteria.longitude is not None and criteria.radius_km is not None:
            filtered = self._filter_by_radius(
                filtered,
                criteria.latitude,
                criteria.longitude,
                criteria.radius_km
            )
        
        # Filter by start year
        if criteria.start_year is not None:
            filtered = filtered[filtered['FIRSTYEAR'] <= criteria.start_year]
        
        # Filter by end year
        if criteria.end_year is not None:
            filtered = filtered[filtered['LASTYEAR'] >= criteria.end_year]
        
        return filtered
    
    def _filter_by_radius(
        self,
        df: pd.DataFrame,
        center_lat: float,
        center_lon: float,
        radius_km: float
    ) -> pd.DataFrame:
        """
        Filter stations within radius of center point.
        
        Uses Haversine formula for distance calculation.
        
        Args:
            df: Inventory dataframe
            center_lat: Center latitude
            center_lon: Center longitude
            radius_km: Radius in kilometers
            
        Returns:
            Filtered dataframe
        """
        import numpy as np
        
        # Haversine formula
        R = 6371  # Earth radius in km
        
        lat1 = np.radians(center_lat)
        lon1 = np.radians(center_lon)
        lat2 = np.radians(df['LATITUDE'])
        lon2 = np.radians(df['LONGITUDE'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        distance = R * c
        
        return df[distance <= radius_km]
    
    def _aggregate_station_metadata(
        self,
        df: pd.DataFrame
    ) -> List[StationMetadata]:
        """
        Aggregate station metadata from inventory records.
        
        Groups inventory records by station ID and creates StationMetadata
        objects with aggregated information.
        
        Args:
            df: Filtered inventory dataframe
            
        Returns:
            List of StationMetadata objects
        """
        stations = []
        
        # Group by station ID
        grouped = df.groupby('ID')
        
        for station_id, group in grouped:
            # Get first record for location info
            first_record = group.iloc[0]
            
            # Aggregate date ranges
            start_year = int(group['FIRSTYEAR'].min())
            end_year = int(group['LASTYEAR'].max())
            
            # Create metadata object (name and coverage will be fetched later if needed)
            metadata = StationMetadata(
                station_id=station_id,
                name=station_id,  # Will be updated when data is fetched
                latitude=float(first_record['LATITUDE']),
                longitude=float(first_record['LONGITUDE']),
                elevation=None,  # Not available in inventory
                start_date=start_year,
                end_date=end_year,
                data_coverage=0.0  # Will be calculated when data is fetched
            )
            
            stations.append(metadata)
        
        return stations

    
    def download_station_data(
        self,
        station: StationMetadata,
        progress_callback: Optional[callable] = None
    ) -> Result:
        """
        Download to temp location, validate, then move to project folder.
        
        Downloads station data to a temporary location, validates the data,
        and moves it to the project folder only if validation passes.
        Automatically cleans up temporary files on success or failure.
        
        Args:
            station: StationMetadata for the station to download
            progress_callback: Optional callback for progress updates
            
        Returns:
            Result object containing:
            - success: True if download and validation succeeded
            - value: DataFrame with precipitation data if successful
            - error: Error message if failed
        """
        # Check if project folder is set
        if not self.app_state.has_project_folder():
            return Result(
                success=False,
                error="No project folder selected. Please select a project folder first."
            )
        
        temp_file = None
        
        try:
            logger.info(f"Starting download for station {station.station_id}")
            
            if progress_callback:
                progress_callback(0, "Initializing download...")
            
            # Create temporary file path
            temp_file = self.temp_download_path / f"{station.station_id}_temp.csv"
            
            # Use GHCNData to fetch station data
            ghcn_data = GHCNData()
            
            if progress_callback:
                progress_callback(30, "Fetching data from GHCN...")
            
            # Fetch data (this downloads and parses the data)
            ghcn_data.fetch(station.station_id)
            
            if ghcn_data.data is None:
                return Result(
                    success=False,
                    error=f"Failed to fetch data for station {station.station_id}"
                )
            
            if progress_callback:
                progress_callback(60, "Validating data...")
            
            # Validate downloaded data
            is_valid, error_msg = self._validate_data(ghcn_data.data)
            if not is_valid:
                return Result(
                    success=False,
                    error=f"Data validation failed: {error_msg}"
                )
            
            if progress_callback:
                progress_callback(80, "Saving to project folder...")
            
            # Save to temporary location first
            ghcn_data.save_to_csv(str(temp_file))
            
            # Move to project folder
            project_data_dir = self.app_state.project_folder / 'data'
            project_data_dir.mkdir(parents=True, exist_ok=True)
            
            final_file = project_data_dir / f"{station.station_id}_data.csv"
            shutil.move(str(temp_file), str(final_file))
            
            logger.info(f"Data saved to {final_file}")
            
            # Update station metadata with actual values
            station.name = ghcn_data.get_name()
            station.data_coverage = ghcn_data.get_coverage()
            
            # Update app state
            self.app_state.set_current_station(station)
            self.app_state.set_precipitation_data(ghcn_data.data)
            
            if progress_callback:
                progress_callback(100, "Download complete!")
            
            return Result(
                success=True,
                value=ghcn_data.data,
                error=None
            )
            
        except requests.RequestException as e:
            logger.error(f"Network error during download: {e}", exc_info=True)
            self._cleanup_temp_file(temp_file)
            return Result(
                success=False,
                error=f"Network Error\n\n"
                      f"Unable to download data from NOAA GHCN database.\n\n"
                      f"Station: {station.station_id}\n"
                      f"Details: {str(e)}\n\n"
                      f"Suggestions:\n"
                      f"• Check your internet connection\n"
                      f"• Verify firewall settings allow HTTPS connections\n"
                      f"• Try again in a few moments"
            )
        except PermissionError as e:
            logger.error(f"Permission error during download: {e}", exc_info=True)
            self._cleanup_temp_file(temp_file)
            return Result(
                success=False,
                error=f"Permission Denied\n\n"
                      f"Cannot write to project folder:\n{self.app_state.project_folder}\n\n"
                      f"Details: {str(e)}\n\n"
                      f"Suggestions:\n"
                      f"• Check folder permissions\n"
                      f"• Ensure the folder is not read-only\n"
                      f"• Try selecting a different project folder"
            )
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}", exc_info=True)
            self._cleanup_temp_file(temp_file)
            return Result(
                success=False,
                error=f"Unexpected Error\n\n"
                      f"An error occurred while downloading station data.\n\n"
                      f"Station: {station.station_id}\n"
                      f"Details: {str(e)}\n\n"
                      f"Please check the log file for more information."
            )
    
    def _validate_data(self, data: pd.DataFrame) -> Tuple[bool, Optional[str]]:
        """
        Validate downloaded precipitation data.
        
        Checks that the data has the required columns and contains
        valid precipitation values.
        
        Args:
            data: DataFrame to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if data is empty
        if data is None or data.empty:
            return False, "Data is empty"
        
        # Check for required columns
        required_columns = ['DATE', 'PRCP']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
        
        # Check if PRCP column has any non-null values
        if data['PRCP'].isna().all():
            return False, "No precipitation data available"
        
        # Check for reasonable data coverage (at least 10% non-null)
        coverage = data['PRCP'].notna().sum() / len(data)
        if coverage < 0.1:
            return False, f"Insufficient data coverage: {coverage*100:.1f}%"
        
        return True, None
    
    def _cleanup_temp_file(self, temp_file: Optional[Path]) -> None:
        """
        Remove a temporary file if it exists.
        
        Args:
            temp_file: Path to temporary file
        """
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
                logger.info(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_file}: {e}")
    
    def cleanup_temp_files(self) -> None:
        """
        Remove any partial downloads from temporary directory.
        
        Cleans up all temporary files in the download directory.
        Should be called on application shutdown or when cleaning up
        after failed operations.
        """
        try:
            if self.temp_download_path.exists():
                # Remove all files in temp directory
                for file in self.temp_download_path.glob("*"):
                    try:
                        if file.is_file():
                            file.unlink()
                            logger.info(f"Cleaned up temporary file: {file}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up {file}: {e}")
                
                # Try to remove the directory itself
                try:
                    self.temp_download_path.rmdir()
                    logger.info(f"Removed temporary directory: {self.temp_download_path}")
                except OSError:
                    # Directory not empty or other error - that's okay
                    pass
                    
        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}")
    
    def calculate_historical_parameters(self, data: pd.DataFrame) -> Result:
        """
        Calculate historical parameters using precipgen.core module.
        
        Delegates to precipgen.core.calculate_params() to compute monthly
        alpha, beta, and transition probability parameters from historical
        precipitation data. Stores the calculated parameters in AppState
        and saves them to the project folder.
        
        Args:
            data: DataFrame with precipitation time series (DATE index, PRCP column)
            
        Returns:
            Result object containing:
            - success: True if calculation succeeded
            - value: HistoricalParameters object if successful
            - error: Error message if failed
        """
        try:
            logger.info("Calculating historical parameters...")
            
            # Validate input data
            if data is None or data.empty:
                return Result(
                    success=False,
                    error="No precipitation data available for parameter calculation"
                )
            
            # Ensure data has required columns
            if 'DATE' not in data.columns and not isinstance(data.index, pd.DatetimeIndex):
                return Result(
                    success=False,
                    error="Data must have DATE column or DatetimeIndex"
                )
            
            if 'PRCP' not in data.columns:
                return Result(
                    success=False,
                    error="Data must have PRCP column"
                )
            
            # Prepare data for calculation (ensure DATE is index)
            calc_data = data.copy()
            if 'DATE' in calc_data.columns:
                calc_data['DATE'] = pd.to_datetime(calc_data['DATE'])
                calc_data.set_index('DATE', inplace=True)
            elif not isinstance(calc_data.index, pd.DatetimeIndex):
                calc_data.index = pd.to_datetime(calc_data.index)
            
            # Calculate parameters using precipgen.core
            params_df = calculate_params(calc_data)
            
            # Validate that we got results
            if params_df is None or params_df.empty:
                return Result(
                    success=False,
                    error="Parameter calculation returned no results"
                )
            
            # Validate parameter ranges (Requirements 4.3)
            validation_result = self._validate_parameter_ranges(params_df)
            if not validation_result[0]:
                logger.warning(f"Parameter validation warning: {validation_result[1]}")
            
            # Extract individual parameter series
            # calculate_params returns DataFrame with columns: PWW, PWD, ALPHA, BETA
            # P(D|W) = 1 - P(W|W), P(D|D) = 1 - P(W|D)
            alpha_series = params_df['ALPHA']
            beta_series = params_df['BETA']
            pww_series = params_df['PWW']
            pwd_series = params_df['PWD']
            pdw_series = 1.0 - pww_series  # P(D|W) = 1 - P(W|W)
            pdd_series = 1.0 - pwd_series  # P(D|D) = 1 - P(W|D)
            
            # Get date range from data
            start_date = calc_data.index.min().date()
            end_date = calc_data.index.max().date()
            
            # Get station ID from app state
            station_id = "unknown"
            if self.app_state.current_station:
                station_id = self.app_state.current_station.station_id
            
            # Create HistoricalParameters object
            historical_params = HistoricalParameters(
                alpha=alpha_series.to_frame(name='ALPHA'),
                beta=beta_series.to_frame(name='BETA'),
                p_wet_wet=pww_series.to_frame(name='PWW'),
                p_wet_dry=pwd_series.to_frame(name='PWD'),
                p_dry_wet=pdw_series.to_frame(name='PDW'),
                p_dry_dry=pdd_series.to_frame(name='PDD'),
                calculation_date=datetime.now(),
                source_station=station_id,
                date_range=(start_date, end_date)
            )
            
            # Store in AppState (Requirements 4.1)
            self.app_state.set_historical_params(historical_params)
            
            # Save to project folder (Requirements 4.5)
            if self.app_state.has_project_folder():
                self._save_parameters_to_project(historical_params, params_df)
            
            logger.info("Historical parameters calculated successfully")
            
            return Result(
                success=True,
                value=historical_params,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error calculating historical parameters: {e}", exc_info=True)
            return Result(
                success=False,
                error=f"Parameter Calculation Error\n\n"
                      f"Failed to calculate historical parameters from precipitation data.\n\n"
                      f"Details: {str(e)}\n\n"
                      f"Suggestions:\n"
                      f"• Verify the downloaded data is complete\n"
                      f"• Check that the data has sufficient coverage\n"
                      f"• Try downloading data for a different time period"
            )
    
    def _validate_parameter_ranges(
        self,
        params_df: pd.DataFrame
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that calculated parameters are within physically reasonable ranges.
        
        Checks that:
        - Alpha > 0
        - Beta > 0
        - 0 <= probabilities <= 1
        
        Args:
            params_df: DataFrame with calculated parameters
            
        Returns:
            Tuple of (is_valid, warning_message)
        """
        warnings = []
        
        # Check alpha values
        if (params_df['ALPHA'] <= 0).any():
            warnings.append("Some alpha values are <= 0")
        if (params_df['ALPHA'] > 5.0).any():
            warnings.append("Some alpha values exceed typical range (0.1-5.0)")
        
        # Check beta values
        if (params_df['BETA'] <= 0).any():
            warnings.append("Some beta values are <= 0")
        if (params_df['BETA'] > 5.0).any():
            warnings.append("Some beta values exceed typical range (0.1-5.0)")
        
        # Check probability values
        if (params_df['PWW'] < 0).any() or (params_df['PWW'] > 1).any():
            warnings.append("Some P(W|W) values are outside [0,1]")
        if (params_df['PWD'] < 0).any() or (params_df['PWD'] > 1).any():
            warnings.append("Some P(W|D) values are outside [0,1]")
        
        if warnings:
            return False, "; ".join(warnings)
        
        return True, None
    
    def _save_parameters_to_project(
        self,
        params: HistoricalParameters,
        params_df: pd.DataFrame
    ) -> None:
        """
        Save calculated parameters to project folder.
        
        Args:
            params: HistoricalParameters object
            params_df: DataFrame with all parameters
        """
        try:
            # Create parameters directory in project folder
            params_dir = self.app_state.project_folder / 'parameters'
            params_dir.mkdir(parents=True, exist_ok=True)
            
            # Save parameters as CSV
            output_file = params_dir / f"{params.source_station}_historical_params.csv"
            params_df.to_csv(output_file)
            
            # Save metadata as separate file
            metadata_file = params_dir / f"{params.source_station}_metadata.txt"
            with open(metadata_file, 'w') as f:
                f.write(f"Station: {params.source_station}\n")
                f.write(f"Calculation Date: {params.calculation_date.isoformat()}\n")
                f.write(f"Data Range: {params.date_range[0]} to {params.date_range[1]}\n")
            
            logger.info(f"Parameters saved to {output_file}")
            
        except Exception as e:
            logger.warning(f"Failed to save parameters to project folder: {e}")
