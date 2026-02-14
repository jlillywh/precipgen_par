"""
Application state management for PrecipGen Desktop.

This module handles runtime application state with observer pattern support
for state change notifications. State is not persisted - use SessionConfig
for persistent configuration.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import pandas as pd


class AppState:
    """
    Runtime application state management with observer pattern.
    
    Manages the current state of the application including project folder,
    station data, precipitation data, and calculated parameters. Notifies
    registered observers when state changes occur.
    
    This class does NOT persist state - use SessionConfig for persistence.
    
    Attributes:
        project_folder: Currently selected project folder path
        current_station: Metadata for the currently selected GHCN station
        precipitation_data: Downloaded precipitation time series data
        historical_params: Parameters calculated from historical data
        adjusted_params: User-adjusted parameters for calibration
    """
    
    def __init__(self):
        """Initialize AppState with empty values and observer list."""
        self.project_folder: Optional[Path] = None
        self.current_station: Optional[Any] = None  # StationMetadata type
        self.precipitation_data: Optional[pd.DataFrame] = None
        self.historical_params: Optional[Any] = None  # HistoricalParameters type
        self.adjusted_params: Optional[Any] = None  # AdjustedParameters type
        
        # New state properties for GUI refactor
        self.basic_analysis_results: Optional[Any] = None  # BasicAnalysisResults type
        self.markov_parameters: Optional[Any] = None  # MarkovParameters type
        self.trend_analysis_results: Optional[Any] = None  # TrendAnalysisResults type
        self.selected_station: Optional[str] = None  # For cross-tab persistence
        self.available_stations: List[str] = []  # List of CSV files in working directory
        
        # Observer pattern: list of callbacks to notify on state changes
        self._observers: List[Callable[[str, Any], None]] = []
    
    def set_project_folder(self, folder: Path) -> None:
        """
        Update project folder and notify observers.
        
        Args:
            folder: Path to the new project folder
        """
        self.project_folder = folder
        self._notify_observers('project_folder', folder)
    
    def set_current_station(self, station: Any) -> None:
        """
        Update current station and notify observers.
        
        Args:
            station: StationMetadata object for the selected station
        """
        self.current_station = station
        self._notify_observers('current_station', station)
    
    def set_precipitation_data(self, data: pd.DataFrame) -> None:
        """
        Update precipitation data and notify observers.
        
        Args:
            data: DataFrame containing precipitation time series
        """
        self.precipitation_data = data
        self._notify_observers('precipitation_data', data)
    
    def set_historical_params(self, params: Any) -> None:
        """
        Update historical parameters and notify observers.
        
        Args:
            params: HistoricalParameters object with calculated values
        """
        self.historical_params = params
        self._notify_observers('historical_params', params)
    
    def set_adjusted_params(self, params: Any) -> None:
        """
        Update adjusted parameters and notify observers.
        
        Args:
            params: AdjustedParameters object with user-modified values
        """
        self.adjusted_params = params
        self._notify_observers('adjusted_params', params)
    
    def set_basic_analysis_results(self, results: Any) -> None:
        """
        Update basic analysis results and notify observers.
        
        Args:
            results: BasicAnalysisResults object with calculated statistics
        """
        self.basic_analysis_results = results
        self._notify_observers('basic_analysis_results', results)
    
    def set_markov_parameters(self, params: Any) -> None:
        """
        Update Markov parameters and notify observers.
        
        Args:
            params: MarkovParameters object with calculated values
        """
        self.markov_parameters = params
        self._notify_observers('markov_parameters', params)
    
    def set_trend_analysis_results(self, results: Any) -> None:
        """
        Update trend analysis results and notify observers.
        
        Args:
            results: TrendAnalysisResults object with seasonal trends
        """
        self.trend_analysis_results = results
        self._notify_observers('trend_analysis_results', results)
    
    def set_selected_station(self, station_file: str) -> None:
        """
        Update selected station and notify observers.
        
        Args:
            station_file: Name of the selected station CSV file
        """
        self.selected_station = station_file
        self._notify_observers('selected_station', station_file)
    
    def set_available_stations(self, stations: List[str]) -> None:
        """
        Update available stations list and notify observers.
        
        Args:
            stations: List of CSV filenames in working directory
        """
        self.available_stations = stations
        self._notify_observers('available_stations', stations)
    
    def register_observer(self, callback: Callable[[str, Any], None]) -> None:
        """
        Register callback for state change notifications.
        
        The callback will be invoked whenever any state property changes.
        Callback signature: callback(state_key: str, new_value: Any)
        
        Args:
            callback: Function to call when state changes.
                     Receives state_key (str) and new_value (Any) as arguments.
        """
        if callback not in self._observers:
            self._observers.append(callback)
    
    def unregister_observer(self, callback: Callable[[str, Any], None]) -> None:
        """
        Remove a previously registered observer callback.
        
        Args:
            callback: The callback function to remove
        """
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self, state_key: str, new_value: Any) -> None:
        """
        Notify all registered observers of a state change.
        
        Args:
            state_key: Name of the state property that changed
            new_value: New value of the state property
        """
        for observer in self._observers:
            try:
                observer(state_key, new_value)
            except Exception as e:
                # Log error but don't let one observer failure affect others
                print(f"Warning: Observer callback failed for {state_key}: {e}")
    
    def clear_all(self) -> None:
        """
        Clear all state values and notify observers.
        
        Useful when starting a new project or resetting the application.
        """
        self.project_folder = None
        self.current_station = None
        self.precipitation_data = None
        self.historical_params = None
        self.adjusted_params = None
        self.basic_analysis_results = None
        self.markov_parameters = None
        self.trend_analysis_results = None
        self.selected_station = None
        self.available_stations = []
        
        # Notify observers of the clear operation
        self._notify_observers('clear_all', None)
    
    def has_project_folder(self) -> bool:
        """Check if a project folder is currently set."""
        return self.project_folder is not None
    
    def has_precipitation_data(self) -> bool:
        """Check if precipitation data is currently loaded."""
        return self.precipitation_data is not None
    
    def has_historical_params(self) -> bool:
        """Check if historical parameters have been calculated."""
        return self.historical_params is not None
    
    def has_adjusted_params(self) -> bool:
        """Check if parameters have been adjusted by the user."""
        return self.adjusted_params is not None
    
    def has_basic_analysis_results(self) -> bool:
        """Check if basic analysis results are available."""
        return self.basic_analysis_results is not None
    
    def has_markov_parameters(self) -> bool:
        """Check if Markov parameters have been calculated."""
        return self.markov_parameters is not None
    
    def has_trend_analysis_results(self) -> bool:
        """Check if trend analysis results are available."""
        return self.trend_analysis_results is not None
