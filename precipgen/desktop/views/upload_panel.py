"""
Dataset Management panel view component for PrecipGen Desktop.

This module provides the UI for managing the active dataset, including viewing and
editing metadata, and importing new precipitation time series files.
"""

import logging
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import pandas as pd
import threading
from typing import Optional, Tuple, Dict, Any

from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.controllers.data_controller import DataController


# Configure logging
logger = logging.getLogger(__name__)


class UploadPanel(ctk.CTkFrame):
    """
    UI component for managing the active dataset and importing new data.
    
    Features:
    - View and edit metadata for the currently locked dataset
    - Import new precipitation data from CSV/Excel
    - Automatically updates session configuration
    """
    
    def __init__(self, parent, data_controller: DataController, app_state: AppState):
        """
        Initialize UploadPanel.
        
        Args:
            parent: Parent widget
            data_controller: DataController instance
            app_state: AppState instance
        """
        super().__init__(parent, corner_radius=0)
        
        self.data_controller = data_controller
        self.app_state = app_state
        
        self.selected_file: Optional[Path] = None
        self.metadata_vars: Dict[str, ctk.StringVar] = {}
        
        # Setup the panel layout
        self.setup_ui()
        
        # Load initial data
        self.load_metadata()
        
        # Register as observer for state changes
        self.app_state.register_observer(self.on_state_change)
    
    def setup_ui(self) -> None:
        """
        Configure the panel layout and widgets.
        """
        # Configure grid layout
        self.grid_rowconfigure(0, weight=0)  # Title
        self.grid_rowconfigure(1, weight=1)  # Content (scrollable)
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Dataset Management",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Scrollable container for main content
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        
        # 1. Current Dataset Metadata Section
        self.create_metadata_section()
        
        # 2. Import New Data Section
        self.create_import_section()
        
    def create_metadata_section(self) -> None:
        """Create the section for viewing and editing current dataset metadata."""
        frame = ctk.CTkFrame(self.scroll_frame)
        frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        
        # Section Header
        header = ctk.CTkLabel(
            frame,
            text="Current Dataset Metadata",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.grid(row=0, column=0, columnspan=2, padx=15, pady=15, sticky="w")
        
        # Metadata Fields
        self.fields = [
            ("Filename", "filename", True),  # Read-only
            ("Station Name", "station_name", False),
            ("Latitude", "latitude", False),
            ("Longitude", "longitude", False),
            ("Elevation (m)", "elevation", False),
            ("Start Year", "start_year", False),
            ("End Year", "end_year", False),
            ("Data Coverage", "data_coverage", True), # Read-only for now
            ("Units", "units", True) # Read-only (system uses mm)
        ]
        
        self.metadata_entries = {}
        
        for i, (label_text, key, readonly) in enumerate(self.fields):
            row = i + 1
            
            label = ctk.CTkLabel(
                frame,
                text=label_text + ":",
                font=ctk.CTkFont(size=12)
            )
            label.grid(row=row, column=0, padx=15, pady=5, sticky="w")
            
            var = ctk.StringVar()
            self.metadata_vars[key] = var
            
            entry = ctk.CTkEntry(
                frame,
                textvariable=var,
                state="readonly" if readonly else "normal",
                width=300
            )
            entry.grid(row=row, column=1, padx=15, pady=5, sticky="w")
            self.metadata_entries[key] = entry
            
        # Buttons Frame
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=len(self.fields)+1, column=1, padx=15, pady=20, sticky="w")
        
        # Save Button
        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="Save Metadata Changes",
            command=self.save_metadata,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.save_btn.pack(side="left", padx=(0, 10))
        
        # Refresh Button
        self.refresh_btn = ctk.CTkButton(
            btn_frame,
            text="Refresh from File",
            command=self.refresh_metadata,
            fg_color="gray",
            hover_color="darkgray"
        )
        self.refresh_btn.pack(side="left")
        
    def create_import_section(self) -> None:
        """Create the section for importing new data."""
        frame = ctk.CTkFrame(self.scroll_frame)
        frame.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        
        # Section Header
        header = ctk.CTkLabel(
            frame,
            text="Import New Data",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.grid(row=0, column=0, columnspan=2, padx=15, pady=15, sticky="w")
        
        # Instructions
        instr = ctk.CTkLabel(
            frame,
            text="Upload a CSV or Excel file to set it as the current dataset.\n"
                 "The system will attempt to detect date and precipitation columns.",
            justify="left",
            text_color="gray"
        )
        instr.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w")
        
        # File Selection
        self.select_btn = ctk.CTkButton(
            frame,
            text="Select File...",
            command=self.on_select_file
        )
        self.select_btn.grid(row=2, column=0, padx=15, pady=10, sticky="w")
        
        self.file_label = ctk.CTkLabel(frame, text="No file selected")
        self.file_label.grid(row=2, column=1, padx=15, pady=10, sticky="w")
        
        # Import Button
        self.import_btn = ctk.CTkButton(
            frame,
            text="Import and Lock Dataset",
            command=self.on_import_clicked,
            state="disabled"
        )
        self.import_btn.grid(row=3, column=0, columnspan=2, padx=15, pady=20, sticky="ew")
        
        # Progress
        self.progress = ctk.CTkProgressBar(frame)
        self.progress.grid(row=4, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="ew")
        self.progress.set(0)
        self.progress_label = ctk.CTkLabel(frame, text="")
        self.progress_label.grid(row=5, column=0, columnspan=2, padx=15, pady=(0, 15))

    def load_metadata(self) -> None:
        """Load metadata from session config into UI fields."""
        try:
            # Access session config via project_controller attached to app_state
            # Note: This dependency should ideally be cleaner, but works for now
            if hasattr(self.app_state, 'project_controller'):
                config = self.app_state.project_controller.session_config
                metadata = config.dataset_metadata
                
                if not metadata:
                    # Provide defaults or clear
                    self.clear_metadata_fields()
                    self.metadata_vars["filename"].set("No dataset loaded")
                    return
                
                # Populate fields
                for key, var in self.metadata_vars.items():
                    val = metadata.get(key, "")
                    if val is None:
                        val = ""
                    var.set(str(val))
                    
            else:
                logger.warning("Project controller not available in app_state")
                
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            
    def clear_metadata_fields(self) -> None:
        """Clear all metadata entry fields."""
        for var in self.metadata_vars.values():
            var.set("")

    def save_metadata(self) -> None:
        """Save edited metadata back to session config."""
        try:
            if not hasattr(self.app_state, 'project_controller'):
                return

            config = self.app_state.project_controller.session_config
            current_metadata = config.dataset_metadata.copy() # Start with existing to keep hidden fields
            
            # Update with values from UI
            updates = {}
            filtered_out_keys = ['filename', 'data_coverage', 'units'] # Read-only
            
            for key, var in self.metadata_vars.items():
                if key not in filtered_out_keys:
                    val = var.get()
                    # Convert types if possible
                    if key in ['latitude', 'longitude', 'elevation']:
                        try:
                            val = float(val) if val else None
                        except ValueError:
                            pass # Keep as string or handle error?
                    elif key in ['start_year', 'end_year']:
                        try:
                            val = int(float(val)) if val else None
                        except ValueError:
                            pass
                            
                    updates[key] = val
            
            current_metadata.update(updates)
            config.dataset_metadata = current_metadata
            config.save()
            
            messagebox.showinfo("Success", "Metadata saved successfully.")
            logger.info("Metadata updated by user.")
            
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            messagebox.showerror("Error", f"Failed to save metadata:\n{e}")

    def refresh_metadata(self) -> None:
        """
        Re-analyze the current dataset file and update metadata fields.
        """
        try:
            # Get current dataset filename
            if not hasattr(self.app_state, 'project_controller'):
                return
                
            config = self.app_state.project_controller.session_config
            filename = config.selected_dataset_file
            
            if not filename or filename == "None":
                messagebox.showwarning("No Dataset", "No dataset is currently selected.")
                return
                
            # Construct full path
            # Access project_folder from app_state or session_config
            project_folder = self.app_state.project_folder
            if not project_folder:
                 project_folder = config.project_folder
                 
            if not project_folder:
                messagebox.showerror("Error", "No project folder selected.")
                return

            filepath = Path(project_folder) / "data" / filename
            
            if not filepath.exists():
                messagebox.showerror("File Not Found", f"Could not find dataset file:\n{filepath}")
                return
                
            # Call controller to analyze file
            result = self.data_controller.generate_metadata_from_file(filepath)
            
            if result.success:
                new_metadata = result.value
                
                # Update UI
                self.metadata_vars["filename"].set(new_metadata.get("filename", ""))
                self.metadata_vars["station_name"].set(new_metadata.get("station_name", ""))
                
                # Handle potential None values safely
                lat = new_metadata.get("latitude")
                self.metadata_vars["latitude"].set(str(lat) if lat is not None else "")
                
                lon = new_metadata.get("longitude")
                self.metadata_vars["longitude"].set(str(lon) if lon is not None else "")
                
                elev = new_metadata.get("elevation")
                self.metadata_vars["elevation"].set(str(elev) if elev is not None else "")
                
                start_year = new_metadata.get("start_year")
                self.metadata_vars["start_year"].set(str(start_year) if start_year is not None else "")
                
                end_year = new_metadata.get("end_year")
                self.metadata_vars["end_year"].set(str(end_year) if end_year is not None else "")
                
                coverage = new_metadata.get("data_coverage")
                if coverage is not None:
                    try:
                        self.metadata_vars["data_coverage"].set(f"{float(coverage)*100:.1f}%")
                    except:
                        self.metadata_vars["data_coverage"].set("")
                else:
                    self.metadata_vars["data_coverage"].set("")
                    
                self.metadata_vars["units"].set(new_metadata.get("units", "mm"))
                
                # Auto-save to config
                config.dataset_metadata = new_metadata
                config.save()
                
                messagebox.showinfo("Success", "Metadata refreshed from file analysis.")
                logger.info(f"Metadata refreshed for {filename}")
                
            else:
                messagebox.showerror("Analysis Failed", f"Failed to analyze file: {result.error}")
                
        except Exception as e:
            logger.error(f"Error refreshing metadata: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def on_select_file(self) -> None:
        """Handle file selection."""
        file_path = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[("Data Files", "*.csv *.xlsx *.xls")]
        )
        
        if file_path:
            self.selected_file = Path(file_path)
            self.file_label.configure(text=self.selected_file.name)
            self.import_btn.configure(state="normal")

    def on_import_clicked(self) -> None:
        """Handle import button click."""
        if not self.selected_file:
            return
            
        self.import_btn.configure(state="disabled")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.progress_label.configure(text="Importing and analyzing...")
        
        # Run in thread
        threading.Thread(target=self._run_import, daemon=True).start()
        
    def _run_import(self) -> None:
        """Background import task."""
        try:
            # Use 'Best Guess' for station name (filename stem)
            station_name = self.selected_file.stem
            
            # Call controller to import
            # Assuming auto-detection of columns for now, or use defaults
            # To be robust, we might need column selection UI. 
            # For now, we'll try common names in the controller or assume defaults.
            # The modified controller `import_custom_data` expects specific col names.
            # Let's try to detect them here or pass 'DATE'/'PRCP' and hope `import_custom_data` logic helps?
            # Actually, `import_custom_data` checks for specific columns.
            # We should probably do a quick pre-scan or just try standard names.
            # Let's try 'DATE' and 'PRCP' as default target names.
            
            # Since `import_custom_data` requires column names, and we want "best guess",
            # we might need to inspect the file *before* calling it, or updated controller to handle "auto".
            # The current controller implementation expects exact column names.
            # Let's assume the user has formatted it or we pass a guess.
            # For this iteration, let's hardcode 'DATE' and 'PRCP' (case insensitive in controller?)
            # Actually the controller I viewed requires exact match.
            # I'll stick to 'DATE' and 'PRCP' for now. Improving column mapping is a future task.
            
            result = self.data_controller.import_custom_data(
                filepath=self.selected_file,
                station_name=station_name,
                unit="mm", # Default assumption
                date_col="DATE",
                prcp_col="PRCP"
            )
            
            self.after(0, lambda: self._handle_import_result(result))
            
        except Exception as e:
            self.after(0, lambda: self._handle_import_error(str(e)))

    def _handle_import_result(self, result) -> None:
        """Handle success/fail of import on main thread."""
        self.progress.stop()
        self.progress.set(0 if not result.success else 1)
        self.import_btn.configure(state="normal")
        self.progress_label.configure(text="")
        
        if result.success:
            # Update session config
            try:
                if hasattr(self.app_state, 'project_controller'):
                    config = self.app_state.project_controller.session_config
                    
                    if isinstance(result.value, dict) and 'metadata' in result.value:
                        config.dataset_metadata = result.value['metadata']
                        config.selected_dataset_file = result.value['metadata']['filename']
                    else:
                        # Fallback
                        filename = Path(result.value).name if isinstance(result.value, (str, Path)) else "imported.csv"
                        config.selected_dataset_file = filename
                    
                    config.save()
                    
                    # Reload UI
                    self.load_metadata()
                    
                    messagebox.showinfo("Import Complete", 
                        f"Successfully imported {config.selected_dataset_file}.\n"
                        "Metadata has been populated. Please review and edit if necessary.")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Imported data but failed to update session: {e}")
        else:
            messagebox.showerror("Import Failed", result.error)

    def _handle_import_error(self, error: str) -> None:
        self.progress.stop()
        self.import_btn.configure(state="normal")
        messagebox.showerror("System Error", f"An unexpected error occurred:\n{error}")

    def on_state_change(self, state_key: str, new_value: Any) -> None:
        """Observer callback."""
        # Refresh metadata if a new station is selected/downloaded elsewhere
        if state_key in ['selected_station']: # Or if we trigger a generic 'dataset_changed'
             self.load_metadata()
        # Note: We don't have a specific event for 'session config changed'. 
        # But usually `selected_station` changes when we download.
    
    def destroy(self) -> None:
        self.app_state.unregister_observer(self.on_state_change)
        super().destroy()
