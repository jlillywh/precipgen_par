"""
Data panel view component for PrecipGen Desktop.

This module provides the UI for GHCN data search, results display,
and data download with progress indication.
"""

import logging
import customtkinter as ctk
from typing import List, Optional
from tkinter import messagebox
import threading

from precipgen.desktop.controllers.data_controller import (
    DataController,
    StationMetadata,
    SearchCriteria
)
from precipgen.desktop.models.app_state import AppState


# Configure logging
logger = logging.getLogger(__name__)


class DataPanel(ctk.CTkFrame):
    """
    UI component for GHCN data search and download.
    
    Provides search interface with input fields for location and date range,
    displays search results with station metadata, and handles data download
    with progress indication.
    
    Attributes:
        data_controller: Controller for GHCN data operations
        app_state: Application state manager
        search_frame: Frame containing search input fields
        results_frame: Frame displaying search results
        download_button: Button to initiate data download
        progress_bar: Progress indicator for download operations
    """
    
    def __init__(self, parent, data_controller: DataController, app_state: AppState):
        """
        Initialize DataPanel.
        
        Args:
            parent: Parent widget (typically MainWindow content area)
            data_controller: DataController instance for data operations
            app_state: AppState instance for observing state changes
        """
        super().__init__(parent, corner_radius=0)
        
        self.data_controller = data_controller
        self.app_state = app_state
        
        # Store search results
        self.search_results: List[StationMetadata] = []
        self.selected_station: Optional[StationMetadata] = None
        
        # Setup the panel layout
        self.setup_ui()
        
        # Register as observer for state changes
        self.app_state.register_observer(self.on_state_change)
    
    def setup_ui(self) -> None:
        """
        Configure the panel layout and widgets.
        
        Creates a vertical layout with search interface at top,
        results display in middle, download controls, and parameter display at bottom.
        """
        # Configure grid layout
        self.grid_rowconfigure(1, weight=1)  # Results frame expands
        self.grid_columnconfigure(0, weight=1)
        
        # Title label
        title_label = ctk.CTkLabel(
            self,
            text="GHCN Station Search",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Search frame
        self.search_frame = self.create_search_frame()
        self.search_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # Results frame
        self.results_frame = self.create_results_frame()
        self.results_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        # Download controls frame
        self.download_frame = self.create_download_frame()
        self.download_frame.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        # Historical parameters display frame
        self.params_frame = self.create_params_frame()
        self.params_frame.grid(row=4, column=0, padx=20, pady=(10, 20), sticky="ew")
    
    def create_search_frame(self) -> ctk.CTkFrame:
        """
        Create search interface with input fields.
        
        Returns:
            Frame containing search input fields and search button
        """
        frame = ctk.CTkFrame(self)
        frame.grid_columnconfigure(1, weight=1)
        
        # Location search (latitude/longitude/radius)
        row = 0
        
        # Latitude
        ctk.CTkLabel(frame, text="Latitude:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        self.lat_entry = ctk.CTkEntry(frame, placeholder_text="e.g., 39.05")
        self.lat_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        
        row += 1
        
        # Longitude
        ctk.CTkLabel(frame, text="Longitude:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        self.lon_entry = ctk.CTkEntry(frame, placeholder_text="e.g., -108.55")
        self.lon_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        
        row += 1
        
        # Radius
        ctk.CTkLabel(frame, text="Radius (km):").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        self.radius_entry = ctk.CTkEntry(frame, placeholder_text="e.g., 50")
        self.radius_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        
        row += 1
        
        # Date range
        ctk.CTkLabel(frame, text="Start Year:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        self.start_year_entry = ctk.CTkEntry(frame, placeholder_text="e.g., 1980")
        self.start_year_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        
        row += 1
        
        ctk.CTkLabel(frame, text="End Year:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        self.end_year_entry = ctk.CTkEntry(frame, placeholder_text="e.g., 2020")
        self.end_year_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        
        row += 1
        
        # Search button
        self.search_button = ctk.CTkButton(
            frame,
            text="Search Stations",
            command=self.on_search_clicked
        )
        self.search_button.grid(row=row, column=0, columnspan=2, padx=10, pady=15)
        
        row += 1
        
        # Search progress indicator (Requirement 11.5)
        self.search_progress = ctk.CTkProgressBar(frame)
        self.search_progress.grid(row=row, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        self.search_progress.set(0)
        self.search_progress.grid_remove()  # Hide initially
        
        return frame
    
    def create_results_frame(self) -> ctk.CTkFrame:
        """
        Create results display area.
        
        Returns:
            Frame for displaying search results
        """
        frame = ctk.CTkFrame(self)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Results label
        self.results_label = ctk.CTkLabel(
            frame,
            text="Search results will appear here",
            font=ctk.CTkFont(size=14)
        )
        self.results_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Scrollable results area
        self.results_scrollable = ctk.CTkScrollableFrame(frame)
        self.results_scrollable.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.results_scrollable.grid_columnconfigure(0, weight=1)
        
        return frame
    
    def create_download_frame(self) -> ctk.CTkFrame:
        """
        Create download controls area.
        
        Returns:
            Frame containing download button and progress indicator
        """
        frame = ctk.CTkFrame(self)
        frame.grid_columnconfigure(0, weight=1)
        
        # Download button
        self.download_button = ctk.CTkButton(
            frame,
            text="Download Station Data",
            command=self.on_download_clicked,
            state="disabled"
        )
        self.download_button.grid(row=0, column=0, padx=10, pady=10)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(frame)
        self.progress_bar.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)
        
        # Progress label
        self.progress_label = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.grid(row=2, column=0, padx=10, pady=(0, 10))
        
        return frame
    
    def create_params_frame(self) -> ctk.CTkFrame:
        """
        Create historical parameters display area.
        
        Returns:
            Frame for displaying calculated historical parameters
        """
        frame = ctk.CTkFrame(self)
        frame.grid_columnconfigure(0, weight=1)
        
        # Title label
        params_title = ctk.CTkLabel(
            frame,
            text="Historical Parameters",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        params_title.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Status label (shown when no parameters calculated)
        self.params_status_label = ctk.CTkLabel(
            frame,
            text="Parameters will appear here after downloading and analyzing station data",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.params_status_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        # Scrollable frame for parameter values (hidden initially)
        self.params_scrollable = ctk.CTkScrollableFrame(frame, height=200)
        self.params_scrollable.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.params_scrollable.grid_columnconfigure(0, weight=1)
        self.params_scrollable.grid_remove()  # Hide initially
        
        return frame
    
    def on_search_clicked(self) -> None:
        """
        Handle search button click.
        
        Validates input fields, creates SearchCriteria, and initiates
        station search via DataController.
        """
        # Validate and parse input fields
        try:
            criteria = self.parse_search_criteria()
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return
        
        # Disable search button during search
        self.search_button.configure(state="disabled", text="Searching...")
        
        # Show indeterminate progress indicator (Requirement 11.5)
        self.search_progress.grid()
        self.search_progress.configure(mode="indeterminate")
        self.search_progress.start()
        
        # Run search in background thread to avoid UI freeze
        def search_thread():
            result = self.data_controller.search_stations(criteria)
            
            # Update UI on main thread
            self.after(0, lambda: self.handle_search_result(result))
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def parse_search_criteria(self) -> SearchCriteria:
        """
        Parse and validate search input fields.
        
        Returns:
            SearchCriteria object with validated parameters
            
        Raises:
            ValueError: If input validation fails
        """
        criteria = SearchCriteria()
        
        # Parse latitude
        lat_text = self.lat_entry.get().strip()
        if lat_text:
            try:
                criteria.latitude = float(lat_text)
                if not -90 <= criteria.latitude <= 90:
                    raise ValueError("Latitude must be between -90 and 90")
            except ValueError:
                raise ValueError("Invalid latitude value")
        
        # Parse longitude
        lon_text = self.lon_entry.get().strip()
        if lon_text:
            try:
                criteria.longitude = float(lon_text)
                if not -180 <= criteria.longitude <= 180:
                    raise ValueError("Longitude must be between -180 and 180")
            except ValueError:
                raise ValueError("Invalid longitude value")
        
        # Parse radius
        radius_text = self.radius_entry.get().strip()
        if radius_text:
            try:
                criteria.radius_km = float(radius_text)
                if criteria.radius_km <= 0:
                    raise ValueError("Radius must be positive")
            except ValueError:
                raise ValueError("Invalid radius value")
        
        # Check that if any location field is provided, all are provided
        location_fields = [criteria.latitude, criteria.longitude, criteria.radius_km]
        if any(f is not None for f in location_fields) and not all(f is not None for f in location_fields):
            raise ValueError("Please provide latitude, longitude, AND radius for location search")
        
        # Parse start year
        start_text = self.start_year_entry.get().strip()
        if start_text:
            try:
                criteria.start_year = int(start_text)
                if criteria.start_year < 1800 or criteria.start_year > 2100:
                    raise ValueError("Start year must be between 1800 and 2100")
            except ValueError:
                raise ValueError("Invalid start year")
        
        # Parse end year
        end_text = self.end_year_entry.get().strip()
        if end_text:
            try:
                criteria.end_year = int(end_text)
                if criteria.end_year < 1800 or criteria.end_year > 2100:
                    raise ValueError("End year must be between 1800 and 2100")
            except ValueError:
                raise ValueError("Invalid end year")
        
        # Validate year range
        if criteria.start_year and criteria.end_year:
            if criteria.start_year > criteria.end_year:
                raise ValueError("Start year must be before end year")
        
        return criteria
    
    def handle_search_result(self, result) -> None:
        """
        Handle search result from DataController.
        
        Args:
            result: Result object from search_stations()
        """
        # Stop and hide search progress indicator
        self.search_progress.stop()
        self.search_progress.grid_remove()
        
        # Re-enable search button
        self.search_button.configure(state="normal", text="Search Stations")
        
        if not result.success:
            # Show error message
            messagebox.showerror("Search Failed", result.error)
            return
        
        # Store and display results
        self.search_results = result.value
        self.display_search_results(self.search_results)
    
    def display_search_results(self, stations: List[StationMetadata]) -> None:
        """
        Show station search results.
        
        Displays station metadata including name, location, and data availability
        in a scrollable list with selection capability.
        
        Args:
            stations: List of StationMetadata objects to display
        """
        # Clear previous results
        for widget in self.results_scrollable.winfo_children():
            widget.destroy()
        
        # Update results label
        if not stations:
            self.results_label.configure(text="No stations found matching criteria")
            self.download_button.configure(state="disabled")
            return
        
        self.results_label.configure(text=f"Found {len(stations)} station(s)")
        
        # Display each station as a selectable button
        for i, station in enumerate(stations):
            self.create_station_card(station, i)
    
    def create_station_card(self, station: StationMetadata, index: int) -> None:
        """
        Create a card displaying station metadata.
        
        Args:
            station: StationMetadata to display
            index: Index in results list
        """
        # Create frame for station card
        card = ctk.CTkFrame(self.results_scrollable)
        card.grid(row=index, column=0, padx=5, pady=5, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        
        # Station ID and name
        id_label = ctk.CTkLabel(
            card,
            text=f"Station: {station.station_id}",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        id_label.grid(row=0, column=0, padx=10, pady=(10, 2), sticky="w")
        
        # Location
        location_text = f"Location: {station.latitude:.4f}°, {station.longitude:.4f}°"
        if station.elevation:
            location_text += f" (Elevation: {station.elevation}m)"
        
        location_label = ctk.CTkLabel(
            card,
            text=location_text,
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        location_label.grid(row=1, column=0, padx=10, pady=2, sticky="w")
        
        # Data availability
        availability_text = f"Data: {station.start_date} - {station.end_date}"
        availability_label = ctk.CTkLabel(
            card,
            text=availability_text,
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        availability_label.grid(row=2, column=0, padx=10, pady=2, sticky="w")
        
        # Select button
        select_button = ctk.CTkButton(
            card,
            text="Select",
            width=80,
            command=lambda s=station: self.on_station_selected(s)
        )
        select_button.grid(row=0, column=1, rowspan=3, padx=10, pady=10)
    
    def on_station_selected(self, station: StationMetadata) -> None:
        """
        Handle station selection.
        
        Args:
            station: Selected StationMetadata
        """
        self.selected_station = station
        self.download_button.configure(state="normal")
        
        # Show selection feedback
        messagebox.showinfo(
            "Station Selected",
            f"Selected station: {station.station_id}\n\n"
            f"Click 'Download Station Data' to retrieve precipitation data."
        )
    
    def on_download_clicked(self) -> None:
        """
        Handle download button click with progress indication.
        
        Initiates data download in background thread and updates
        progress bar based on download status.
        """
        if not self.selected_station:
            messagebox.showwarning("No Station Selected", "Please select a station first")
            return
        
        # Check if project folder is set
        if not self.app_state.has_project_folder():
            messagebox.showerror(
                "No Project Folder",
                "Please select a project folder before downloading data"
            )
            return
        
        # Disable download button during download
        self.download_button.configure(state="disabled")
        
        # Reset and configure progress bar for determinate mode (Requirement 11.5)
        self.progress_bar.stop()  # Stop any previous indeterminate animation
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting download...")
        
        # Run download in background thread
        def download_thread():
            def progress_callback(percent, message):
                # Update progress on main thread
                self.after(0, lambda: self.update_progress(percent / 100.0, message))
            
            result = self.data_controller.download_station_data(
                self.selected_station,
                progress_callback
            )
            
            # Handle result on main thread
            self.after(0, lambda: self.handle_download_result(result))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def update_progress(self, value: float, message: str) -> None:
        """
        Update progress bar and label.
        
        Args:
            value: Progress value (0.0 to 1.0)
            message: Progress message to display
        """
        self.progress_bar.set(value)
        self.progress_label.configure(text=message)
    
    def handle_download_result(self, result) -> None:
        """
        Handle download result from DataController.
        
        Args:
            result: Result object from download_station_data()
        """
        if not result.success:
            # Show error message
            self.progress_label.configure(text="Download failed")
            self.progress_bar.set(0)
            # Re-enable download button
            self.download_button.configure(state="normal")
            messagebox.showerror("Download Failed", result.error)
            return
        
        # Success - now calculate historical parameters
        # Show indeterminate progress for calculation (Requirement 11.5)
        self.progress_label.configure(text="Calculating parameters...")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        # Calculate parameters in background thread
        def calculate_thread():
            calc_result = self.data_controller.calculate_historical_parameters(result.value)
            
            # Handle result on main thread
            self.after(0, lambda: self.handle_calculation_result(calc_result))
        
        threading.Thread(target=calculate_thread, daemon=True).start()
    
    def handle_calculation_result(self, result) -> None:
        """
        Handle parameter calculation result.
        
        Args:
            result: Result object from calculate_historical_parameters()
        """
        # Stop indeterminate progress and reset to determinate mode
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        
        # Re-enable download button
        self.download_button.configure(state="normal")
        
        if not result.success:
            # Show error but don't fail the download
            self.progress_label.configure(text="Download complete (parameter calculation failed)")
            self.progress_bar.set(1.0)
            messagebox.showwarning(
                "Parameter Calculation Failed",
                f"Data downloaded successfully, but parameter calculation failed:\n\n{result.error}"
            )
            return
        
        # Success
        self.progress_label.configure(text="Download and analysis complete!")
        self.progress_bar.set(1.0)
        messagebox.showinfo(
            "Download Complete",
            f"Successfully downloaded and analyzed data for station {self.selected_station.station_id}\n\n"
            f"Historical parameters have been calculated and are displayed below."
        )
    
    def on_state_change(self, state_key: str, new_value) -> None:
        """
        React to application state changes.
        
        Args:
            state_key: Name of the state property that changed
            new_value: New value of the state property
        """
        # Update parameter display when historical parameters are calculated
        if state_key == 'historical_params' and new_value is not None:
            self.display_historical_parameters(new_value)
    
    def display_historical_parameters(self, params) -> None:
        """
        Display calculated historical parameters.
        
        Shows α, β, and transition probabilities in a formatted table.
        Updates the UI to show parameter values when they are calculated.
        
        Args:
            params: HistoricalParameters object with calculated values
        """
        # Hide status label and show scrollable frame
        self.params_status_label.grid_remove()
        self.params_scrollable.grid()
        
        # Clear previous parameter display
        for widget in self.params_scrollable.winfo_children():
            widget.destroy()
        
        # Create header row
        header_frame = ctk.CTkFrame(self.params_scrollable)
        header_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        header_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)
        
        headers = ["Month", "α (Alpha)", "β (Beta)", "P(W|W)", "P(W|D)", "P(D|W)", "P(D|D)"]
        for col, header in enumerate(headers):
            label = ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            label.grid(row=0, column=col, padx=5, pady=5)
        
        # Month names
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        # Display parameter values for each month
        for month_idx in range(12):
            row_frame = ctk.CTkFrame(self.params_scrollable)
            row_frame.grid(row=month_idx + 1, column=0, padx=5, pady=2, sticky="ew")
            row_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)
            
            # Month name
            month_label = ctk.CTkLabel(
                row_frame,
                text=month_names[month_idx],
                font=ctk.CTkFont(size=11)
            )
            month_label.grid(row=0, column=0, padx=5, pady=3)
            
            # Extract values for this month (month_idx is 0-based, but DataFrame index is 1-based)
            month_num = month_idx + 1
            
            # Alpha
            alpha_val = params.alpha.loc[month_num, 'ALPHA'] if month_num in params.alpha.index else 0.0
            alpha_label = ctk.CTkLabel(
                row_frame,
                text=f"{alpha_val:.3f}",
                font=ctk.CTkFont(size=11)
            )
            alpha_label.grid(row=0, column=1, padx=5, pady=3)
            
            # Beta
            beta_val = params.beta.loc[month_num, 'BETA'] if month_num in params.beta.index else 0.0
            beta_label = ctk.CTkLabel(
                row_frame,
                text=f"{beta_val:.3f}",
                font=ctk.CTkFont(size=11)
            )
            beta_label.grid(row=0, column=2, padx=5, pady=3)
            
            # P(W|W)
            pww_val = params.p_wet_wet.loc[month_num, 'PWW'] if month_num in params.p_wet_wet.index else 0.0
            pww_label = ctk.CTkLabel(
                row_frame,
                text=f"{pww_val:.3f}",
                font=ctk.CTkFont(size=11)
            )
            pww_label.grid(row=0, column=3, padx=5, pady=3)
            
            # P(W|D)
            pwd_val = params.p_wet_dry.loc[month_num, 'PWD'] if month_num in params.p_wet_dry.index else 0.0
            pwd_label = ctk.CTkLabel(
                row_frame,
                text=f"{pwd_val:.3f}",
                font=ctk.CTkFont(size=11)
            )
            pwd_label.grid(row=0, column=4, padx=5, pady=3)
            
            # P(D|W)
            pdw_val = params.p_dry_wet.loc[month_num, 'PDW'] if month_num in params.p_dry_wet.index else 0.0
            pdw_label = ctk.CTkLabel(
                row_frame,
                text=f"{pdw_val:.3f}",
                font=ctk.CTkFont(size=11)
            )
            pdw_label.grid(row=0, column=5, padx=5, pady=3)
            
            # P(D|D)
            pdd_val = params.p_dry_dry.loc[month_num, 'PDD'] if month_num in params.p_dry_dry.index else 0.0
            pdd_label = ctk.CTkLabel(
                row_frame,
                text=f"{pdd_val:.3f}",
                font=ctk.CTkFont(size=11)
            )
            pdd_label.grid(row=0, column=6, padx=5, pady=3)
        
        # Add metadata display
        metadata_frame = ctk.CTkFrame(self.params_scrollable)
        metadata_frame.grid(row=13, column=0, padx=5, pady=(10, 5), sticky="ew")
        
        metadata_text = (
            f"Station: {params.source_station} | "
            f"Data Range: {params.date_range[0]} to {params.date_range[1]} | "
            f"Calculated: {params.calculation_date.strftime('%Y-%m-%d %H:%M')}"
        )
        
        metadata_label = ctk.CTkLabel(
            metadata_frame,
            text=metadata_text,
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        metadata_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
    
    def destroy(self) -> None:
        """
        Clean up resources when panel is destroyed.
        
        Unregisters the state observer before destroying the widget.
        """
        # Unregister observer
        self.app_state.unregister_observer(self.on_state_change)
        
        # Call parent destroy
        super().destroy()
