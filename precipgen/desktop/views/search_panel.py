"""
Search panel view component for PrecipGen Desktop.

This module provides the UI for GHCN station search and data download,
featuring an interactive map for location selection.
"""

import logging
import customtkinter as ctk
from typing import List, Optional
from tkinter import messagebox
import threading
import tkintermapview

from precipgen.desktop.controllers.data_controller import (
    DataController,
    StationMetadata,
    SearchCriteria
)
from precipgen.desktop.models.app_state import AppState


# Configure logging
logger = logging.getLogger(__name__)


class SearchPanel(ctk.CTkFrame):
    """
    UI component for GHCN station search and data download.
    
    Provides search interface with input fields for location,
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
        Initialize SearchPanel.
        
        Args:
            parent: Parent widget (typically MainWindow tab)
            data_controller: DataController instance for data operations
            app_state: AppState instance for observing state changes
        """
        super().__init__(parent, corner_radius=0)
        
        self.data_controller = data_controller
        self.app_state = app_state
        
        # Store search results
        self.search_results: List[StationMetadata] = []
        self.selected_station: Optional[StationMetadata] = None
        
        # Radio button variable for station selection
        self.selected_station_var = ctk.StringVar(value="")
        
        # Map state
        self.current_marker = None
        self.current_circle = None
        self.map_latitude: Optional[float] = None
        self.map_longitude: Optional[float] = None
        
        # Setup the panel layout
        self.setup_ui()
        
        # Register as observer for state changes
        self.app_state.register_observer(self.on_state_change)
    
    def setup_ui(self) -> None:
        """
        Configure the panel layout and widgets.
        
        Creates a vertical layout with search interface at top,
        results display in middle, and download controls at bottom.
        """
        # Configure grid layout - results frame should expand
        self.grid_rowconfigure(2, weight=1)  # Results frame expands
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
    
    def create_search_frame(self) -> ctk.CTkFrame:
        """
        Create search interface with interactive map.
        
        Returns:
            Frame containing map widget and search controls
        """
        frame = ctk.CTkFrame(self)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        
        # Instructions
        instructions = ctk.CTkLabel(
            frame,
            text="Click on the map to select a location, then set the search radius and click Search.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        instructions.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Map widget
        self.map_widget = tkintermapview.TkinterMapView(frame, width=800, height=400, corner_radius=10)
        self.map_widget.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Set initial position (center of USA)
        self.map_widget.set_position(39.8283, -98.5795)
        self.map_widget.set_zoom(4)
        
        # Add click handler
        self.map_widget.add_left_click_map_command(self.on_map_click)
        
        # Controls frame (below map)
        controls_frame = ctk.CTkFrame(frame, fg_color="transparent")
        controls_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        controls_frame.grid_columnconfigure(1, weight=1)
        
        # Coordinate display
        coord_frame = ctk.CTkFrame(controls_frame)
        coord_frame.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(coord_frame, text="Selected Location:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=5, pady=5
        )
        self.coord_label = ctk.CTkLabel(
            coord_frame,
            text="Click on map to select",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.coord_label.grid(row=0, column=1, padx=5, pady=5)
        
        # Radius control
        radius_frame = ctk.CTkFrame(controls_frame)
        radius_frame.grid(row=0, column=1, padx=5, pady=5, sticky="e")
        
        ctk.CTkLabel(radius_frame, text="Search Radius (km):").grid(
            row=0, column=0, padx=5, pady=5
        )
        self.radius_entry = ctk.CTkEntry(radius_frame, placeholder_text="e.g., 50", width=100)
        self.radius_entry.grid(row=0, column=1, padx=5, pady=5)
        self.radius_entry.insert(0, "50")  # Default value
        
        # Bind radius change to update circle
        self.radius_entry.bind("<KeyRelease>", self.on_radius_changed)
        
        # Search button
        self.search_button = ctk.CTkButton(
            frame,
            text="Search Stations",
            command=self.on_search_clicked,
            height=40
        )
        self.search_button.grid(row=3, column=0, padx=10, pady=10)
        
        # Search progress indicator
        self.search_progress = ctk.CTkProgressBar(frame)
        self.search_progress.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")
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
    
    def on_map_click(self, coords) -> None:
        """
        Handle map click event.
        
        Args:
            coords: Tuple of (latitude, longitude)
        """
        lat, lon = coords
        self.map_latitude = lat
        self.map_longitude = lon
        
        # Update coordinate display
        self.coord_label.configure(
            text=f"Lat: {lat:.4f}°, Lon: {lon:.4f}°",
            text_color=("gray10", "gray90")
        )
        
        # Remove old marker if exists
        if self.current_marker:
            self.current_marker.delete()
        
        # Add new marker
        self.current_marker = self.map_widget.set_marker(lat, lon, text="Search Location")
        
        # Update radius circle
        self.update_radius_circle()
        
        logger.info(f"Map location selected: {lat:.4f}, {lon:.4f}")
    
    def on_radius_changed(self, event=None) -> None:
        """
        Handle radius entry change to update circle on map.
        """
        self.update_radius_circle()
    
    def update_radius_circle(self) -> None:
        """
        Update the radius circle on the map based on current radius value.
        """
        if self.map_latitude is None or self.map_longitude is None:
            return
        
        # Get radius value
        try:
            radius_km = float(self.radius_entry.get().strip())
            if radius_km <= 0:
                return
        except (ValueError, AttributeError):
            return
        
        # Remove old circle if exists
        if self.current_circle:
            self.current_circle.delete()
        
        # Add new circle (radius in meters for the API)
        self.current_circle = self.map_widget.set_circle(
            self.map_latitude,
            self.map_longitude,
            radius_km * 1000,  # Convert km to meters
            color="blue",
            fill_color="lightblue",
            border_width=2
        )
    
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
        
        # Show indeterminate progress indicator
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
        Parse and validate search input from map and radius field.
        
        Returns:
            SearchCriteria object with validated parameters
            
        Raises:
            ValueError: If input validation fails
        """
        criteria = SearchCriteria()
        
        # Check if location is selected on map
        if self.map_latitude is None or self.map_longitude is None:
            raise ValueError("Please click on the map to select a search location")
        
        criteria.latitude = self.map_latitude
        criteria.longitude = self.map_longitude
        
        # Parse radius
        radius_text = self.radius_entry.get().strip()
        if not radius_text:
            raise ValueError("Please enter a search radius")
        
        try:
            criteria.radius_km = float(radius_text)
            if criteria.radius_km <= 0:
                raise ValueError("Radius must be positive")
            if criteria.radius_km > 1000:
                raise ValueError("Radius must be 1000 km or less")
        except ValueError as e:
            if "could not convert" in str(e):
                raise ValueError("Invalid radius value. Must be a positive number (in kilometers).")
            raise
        
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
        Create a card displaying station metadata with radio button selection.
        
        Args:
            station: StationMetadata to display
            index: Index in results list
        """
        # Create frame for station card with horizontal layout
        card = ctk.CTkFrame(self.results_scrollable)
        card.grid(row=index, column=0, padx=5, pady=3, sticky="ew")
        card.grid_columnconfigure(1, weight=1)
        
        # Radio button for selection (left side)
        radio_button = ctk.CTkRadioButton(
            card,
            text="",
            variable=self.selected_station_var,
            value=station.station_id,
            command=lambda: self.on_station_selected(station)
        )
        radio_button.grid(row=0, column=0, padx=(10, 5), pady=8)
        
        # Create horizontal layout for all info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=1, padx=5, pady=8, sticky="ew")
        info_frame.grid_columnconfigure(0, weight=0)  # Station ID
        info_frame.grid_columnconfigure(1, weight=0)  # Separator
        info_frame.grid_columnconfigure(2, weight=0)  # Location
        info_frame.grid_columnconfigure(3, weight=0)  # Separator
        info_frame.grid_columnconfigure(4, weight=0)  # Data range
        info_frame.grid_columnconfigure(5, weight=1)  # Spacer
        
        # Station ID and Name (bold)
        id_name_text = f"{station.station_id}"
        if station.name and station.name != station.station_id:
            id_name_text += f" - {station.name}"
        
        id_label = ctk.CTkLabel(
            info_frame,
            text=id_name_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        id_label.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        # Separator
        sep1 = ctk.CTkLabel(info_frame, text="|", text_color="gray")
        sep1.grid(row=0, column=1, padx=5)
        
        # Location (compact format)
        location_text = f"Lat: {station.latitude:.4f}°, Lon: {station.longitude:.4f}°"
        if station.elevation:
            location_text += f", Elev: {station.elevation}m"
        
        location_label = ctk.CTkLabel(
            info_frame,
            text=location_text,
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        location_label.grid(row=0, column=2, padx=(0, 10), sticky="w")
        
        # Separator
        sep2 = ctk.CTkLabel(info_frame, text="|", text_color="gray")
        sep2.grid(row=0, column=3, padx=5)
        
        # Data availability (compact format)
        availability_text = f"Data: {station.start_date}-{station.end_date}"
        availability_label = ctk.CTkLabel(
            info_frame,
            text=availability_text,
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        availability_label.grid(row=0, column=4, padx=(0, 10), sticky="w")
    
    def on_station_selected(self, station: StationMetadata) -> None:
        """
        Handle station selection via radio button.
        
        Args:
            station: Selected StationMetadata
        """
        self.selected_station = station
        self.download_button.configure(state="normal")
        
        logger.info(f"Station selected: {station.station_id}")
    
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
        
        # Reset and configure progress bar for determinate mode
        self.progress_bar.stop()
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
        # Show indeterminate progress for calculation
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
        
        This runs on the main thread to safely update UI.
        
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
        
        # Success - update app state on main thread to trigger observers safely
        if result.value:
            self.app_state.set_historical_params(result.value)
        
        self.progress_label.configure(text="Download and analysis complete!")
        self.progress_bar.set(1.0)
        messagebox.showinfo(
            "Download Complete",
            f"Successfully downloaded and analyzed data for station {self.selected_station.station_id}\n\n"
            f"View the calculated parameters in the 'Parameters' tab."
        )
    
    def on_state_change(self, state_key: str, new_value) -> None:
        """
        React to application state changes.
        
        Args:
            state_key: Name of the state property that changed
            new_value: New value of the state property
        """
        # No specific state changes to handle in search panel
        pass
    
    def destroy(self) -> None:
        """
        Clean up resources when panel is destroyed.
        
        Unregisters the state observer before destroying the widget.
        """
        # Unregister observer
        self.app_state.unregister_observer(self.on_state_change)
        
        # Call parent destroy
        super().destroy()
