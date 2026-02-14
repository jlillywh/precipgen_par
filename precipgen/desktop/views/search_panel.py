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
        Configure the panel layout with side-by-side design.
        
        Left side: Controls, station list, and download button
        Right side: Interactive map
        """
        # Configure grid layout - two columns
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)  # Left side (controls + results)
        self.grid_columnconfigure(1, weight=2)  # Right side (map) - wider
        
        # LEFT SIDE - Controls and Results
        left_panel = ctk.CTkFrame(self)
        left_panel.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")
        left_panel.grid_rowconfigure(2, weight=1)  # Results expand
        left_panel.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            left_panel,
            text="GHCN Station Search",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Instructions
        instructions = ctk.CTkLabel(
            left_panel,
            text="Click on the map to select a location",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        instructions.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")
        
        # Search controls
        self.create_search_controls(left_panel)
        
        # Results frame
        self.results_frame = self.create_results_frame(left_panel)
        self.results_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        
        # Download button
        self.download_button = ctk.CTkButton(
            left_panel,
            text="Download Station Data",
            command=self.on_download_clicked,
            state="disabled",
            height=40
        )
        self.download_button.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(left_panel)
        self.progress_bar.grid(row=5, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.progress_bar.set(0)
        
        # Progress label
        self.progress_label = ctk.CTkLabel(
            left_panel,
            text="",
            font=ctk.CTkFont(size=11)
        )
        self.progress_label.grid(row=6, column=0, padx=10, pady=(0, 10))
        
        # RIGHT SIDE - Map
        right_panel = ctk.CTkFrame(self)
        right_panel.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        # Map widget
        self.map_widget = tkintermapview.TkinterMapView(right_panel, corner_radius=10)
        self.map_widget.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Set initial position (center of USA)
        self.map_widget.set_position(39.8283, -98.5795)
        self.map_widget.set_zoom(4)
        
        # Add click handler
        self.map_widget.add_left_click_map_command(self.on_map_click)
    
    def create_search_controls(self, parent) -> None:
        """Create search control widgets in the left panel."""
        controls_frame = ctk.CTkFrame(parent)
        controls_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        controls_frame.grid_columnconfigure(1, weight=1)
        
        # Coordinate display
        ctk.CTkLabel(
            controls_frame,
            text="Location:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.coord_label = ctk.CTkLabel(
            controls_frame,
            text="Click on map",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.coord_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Radius control
        ctk.CTkLabel(
            controls_frame,
            text="Radius (km):",
            font=ctk.CTkFont(size=11, weight="bold")
        ).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        self.radius_entry = ctk.CTkEntry(controls_frame, placeholder_text="50", width=80)
        self.radius_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.radius_entry.insert(0, "50")
        self.radius_entry.bind("<KeyRelease>", self.on_radius_changed)
        
        # Min Years control
        ctk.CTkLabel(
            controls_frame,
            text="Min Years:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        self.min_years_entry = ctk.CTkEntry(controls_frame, placeholder_text="30", width=80)
        self.min_years_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.min_years_entry.insert(0, "30")
        
        # Search button
        self.search_button = ctk.CTkButton(
            controls_frame,
            text="Search Stations",
            command=self.on_search_clicked,
            height=35
        )
        self.search_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10, sticky="ew")
        
        # Search progress
        self.search_progress = ctk.CTkProgressBar(controls_frame)
        self.search_progress.grid(row=4, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="ew")
        self.search_progress.set(0)
        self.search_progress.grid_remove()
    
    def create_results_frame(self, parent) -> ctk.CTkFrame:
        """
        Create results display area.
        
        Args:
            parent: Parent widget
            
        Returns:
            Frame for displaying search results
        """
        frame = ctk.CTkFrame(parent)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Results label
        self.results_label = ctk.CTkLabel(
            frame,
            text="Search results will appear here",
            font=ctk.CTkFont(size=12)
        )
        self.results_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Scrollable results area
        self.results_scrollable = ctk.CTkScrollableFrame(frame, height=200)
        self.results_scrollable.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.results_scrollable.grid_columnconfigure(0, weight=1)
        
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
        
        # Create circle as a polygon (approximate with 64 points)
        import math
        num_points = 64
        circle_points = []
        
        # Earth radius in km
        earth_radius = 6371.0
        
        # Convert radius to degrees (approximate)
        lat_rad = math.radians(self.map_latitude)
        radius_deg_lat = radius_km / 111.0  # 1 degree latitude ≈ 111 km
        radius_deg_lon = radius_km / (111.0 * math.cos(lat_rad))  # Adjust for longitude
        
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            point_lat = self.map_latitude + radius_deg_lat * math.sin(angle)
            point_lon = self.map_longitude + radius_deg_lon * math.cos(angle)
            circle_points.append((point_lat, point_lon))
        
        # Draw the circle as a polygon
        try:
            self.current_circle = self.map_widget.set_polygon(
                circle_points,
                fill_color="lightblue",
                outline_color="blue",
                border_width=2,
                name="search_radius"
            )
        except Exception as e:
            logger.warning(f"Could not draw radius circle: {e}")
    
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

        # Parse min years
        min_years_text = self.min_years_entry.get().strip()
        if min_years_text:
            try:
                criteria.min_years = int(min_years_text)
                if criteria.min_years < 0:
                    raise ValueError("Minimum years must be non-negative")
            except ValueError:
                raise ValueError("Invalid minimum years value. Must be an integer.")
        
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
        
        # Get currently locked dataset file from config
        locked_file = self.app_state.project_controller.session_config.selected_dataset_file
        
        # Display each station as a selectable button
        for i, station in enumerate(stations):
            is_locked = False
            if locked_file:
                # Check if this station matches the locked file
                # The file is saved as {station_id}.csv
                station_filename = f"{station.station_id}.csv"
                if station_filename == locked_file:
                    is_locked = True
            
            self.create_station_card(station, i, is_locked)
    
    def create_station_card(self, station: StationMetadata, index: int, is_locked: bool = False) -> None:
        """
        Create a card displaying station metadata with radio button selection.
        
        Args:
            station: StationMetadata to display
            index: Index in results list
            is_locked: True if this is the currently locked dataset
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
            width=20, # Compact width
            command=lambda: self.on_station_selected(station)
        )
        radio_button.grid(row=0, column=0, padx=(5, 5), pady=8, sticky="n") # Reduced padding, align top
        
        # Info Frame (Vertical layout for multi-line text)
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=1, padx=0, pady=5, sticky="ew")
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Row 1: Station ID + Name + Status
        header_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew")
        
        # ID and Name
        id_name_text = f"{station.station_id}"
        if station.name and station.name != station.station_id:
            id_name_text += f" - {station.name}"
            
        header_label = ctk.CTkLabel(
            header_frame,
            text=id_name_text,
            font=ctk.CTkFont(size=12, weight="bold"), # Standard size
            anchor="w"
        )
        header_label.pack(side="left")
        
        # Locked Status
        if is_locked:
            locked_label = ctk.CTkLabel(
                header_frame,
                text="[CURRENT DATASET]",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="green"
            )
            locked_label.pack(side="left", padx=10)
            
        # Row 2: Location and Date Details (Compact, gray)
        details_text = f"Lat: {station.latitude:.4f}°, Lon: {station.longitude:.4f}°"
        if station.elevation:
            details_text += f", Elev: {station.elevation}m"
        
        details_text += f"  |  Data: {station.start_date}-{station.end_date}"
        if station.data_coverage is not None:
             details_text += f" ({station.data_coverage*100:.0f}%)"
             
        details_label = ctk.CTkLabel(
            info_frame,
            text=details_text,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        details_label.grid(row=1, column=0, sticky="w", pady=(0, 0))

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
        # Stop indeterminate progress if running (though download uses determinate)
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        
        # Re-enable download button
        self.download_button.configure(state="normal")
        
        if not result.success:
            # Show error message
            self.progress_label.configure(text="Download failed")
            self.progress_bar.set(0)
            messagebox.showerror("Download Failed", result.error)
            return
        
        # Success
        
        # Update session config to lock this dataset
        try:
            config = self.app_state.project_controller.session_config
            
            # Extract metadata from result
            if isinstance(result.value, dict) and 'metadata' in result.value:
                metadata = result.value['metadata']
                config.dataset_metadata = metadata
                dataset_filename = metadata.get('filename')
                config.selected_dataset_file = dataset_filename
                logger.info(f"Dataset metadata saved: {metadata}")
            else:
                # Fallback for backward compatibility (though controller is updated)
                dataset_filename = f"{self.selected_station.station_id}.csv"
                config.selected_dataset_file = dataset_filename
                logger.warning("No metadata in download result, using default filename")

            config.save()
            logger.info(f"Dataset locked to session: {dataset_filename}")
            
            # Refresh results to show new locked status
            self.display_search_results(self.search_results)
            
        except Exception as e:
            logger.error(f"Failed to update session config with locked dataset: {e}")
        
        self.progress_label.configure(text="Download complete!")
        self.progress_bar.set(1.0)
        
        messagebox.showinfo(
            "Download Complete",
            f"Successfully downloaded data for station {self.selected_station.station_id}\n\n"
            f"The CSV file has been saved to your project folder and set as the current dataset."
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
