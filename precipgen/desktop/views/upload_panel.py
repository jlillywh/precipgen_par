"""
Upload panel view component for PrecipGen Desktop.

This module provides the UI for uploading existing precipitation CSV files.
"""

import logging
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import pandas as pd
import threading
from typing import Optional, Tuple
import re

from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.controllers.data_controller import DataController


# Configure logging
logger = logging.getLogger(__name__)


class UploadPanel(ctk.CTkFrame):
    """
    UI component for uploading precipitation CSV files.
    
    Handles file selection, parsing with flexible format detection,
    unit conversion, and parameter calculation.
    
    Attributes:
        data_controller: Controller for data operations
        app_state: Application state manager
    """
    
    def __init__(self, parent, data_controller: DataController, app_state: AppState):
        """
        Initialize UploadPanel.
        
        Args:
            parent: Parent widget (typically MainWindow tab)
            data_controller: DataController instance for data operations
            app_state: AppState instance for observing state changes
        """
        super().__init__(parent, corner_radius=0)
        
        self.data_controller = data_controller
        self.app_state = app_state
        
        self.selected_file: Optional[Path] = None
        
        # Setup the panel layout
        self.setup_ui()
        
        # Register as observer for state changes
        self.app_state.register_observer(self.on_state_change)
    
    def setup_ui(self) -> None:
        """
        Configure the panel layout and widgets.
        """
        # Configure grid layout
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Title label
        title_label = ctk.CTkLabel(
            self,
            text="Upload Precipitation Data",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Instructions
        instructions = ctk.CTkLabel(
            self,
            text="Upload a CSV file with precipitation time series data.\n"
                 "The file should contain a date column and a precipitation column.\n"
                 "Metadata rows at the top of the file will be automatically detected.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="left"
        )
        instructions.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")
        
        # Upload frame
        self.upload_frame = self.create_upload_frame()
        self.upload_frame.grid(row=2, column=0, padx=20, pady=10, sticky="new")
        
        # Preview frame
        self.preview_frame = self.create_preview_frame()
        self.preview_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        
        # Process button frame
        self.process_frame = self.create_process_frame()
        self.process_frame.grid(row=4, column=0, padx=20, pady=(10, 20), sticky="ew")
    
    def create_upload_frame(self) -> ctk.CTkFrame:
        """
        Create file upload interface.
        
        Returns:
            Frame containing file selection button
        """
        frame = ctk.CTkFrame(self)
        frame.grid_columnconfigure(1, weight=1)
        
        # Select file button
        self.select_button = ctk.CTkButton(
            frame,
            text="Select CSV File",
            command=self.on_select_file_clicked,
            width=150
        )
        self.select_button.grid(row=0, column=0, padx=10, pady=15)
        
        # Selected file label
        self.file_label = ctk.CTkLabel(
            frame,
            text="No file selected",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.file_label.grid(row=0, column=1, padx=10, pady=15, sticky="w")
        
        return frame
    
    def create_preview_frame(self) -> ctk.CTkFrame:
        """
        Create data preview area.
        
        Returns:
            Frame for displaying file preview
        """
        frame = ctk.CTkFrame(self)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Preview label
        self.preview_label = ctk.CTkLabel(
            frame,
            text="File preview will appear here",
            font=ctk.CTkFont(size=14)
        )
        self.preview_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Scrollable preview area
        self.preview_text = ctk.CTkTextbox(frame, height=200, wrap="none")
        self.preview_text.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.preview_text.configure(state="disabled")
        
        return frame
    
    def create_process_frame(self) -> ctk.CTkFrame:
        """
        Create process controls area.
        
        Returns:
            Frame containing process button and progress indicator
        """
        frame = ctk.CTkFrame(self)
        frame.grid_columnconfigure(0, weight=1)
        
        # Process button
        self.process_button = ctk.CTkButton(
            frame,
            text="Process and Calculate Parameters",
            command=self.on_process_clicked,
            state="disabled"
        )
        self.process_button.grid(row=0, column=0, padx=10, pady=10)
        
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
    
    def on_select_file_clicked(self) -> None:
        """
        Handle file selection button click.
        """
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select Precipitation CSV File",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        self.selected_file = Path(file_path)
        self.file_label.configure(text=f"Selected: {self.selected_file.name}")
        
        # Preview the file
        self.preview_file()
        
        # Enable process button
        self.process_button.configure(state="normal")
    
    def preview_file(self) -> None:
        """
        Display a preview of the selected file.
        """
        try:
            # Read first 20 lines for preview
            with open(self.selected_file, 'r') as f:
                lines = f.readlines()[:20]
            
            preview_text = "".join(lines)
            if len(lines) == 20:
                preview_text += "\n... (file continues)"
            
            self.preview_text.configure(state="normal")
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", preview_text)
            self.preview_text.configure(state="disabled")
            
            self.preview_label.configure(text=f"Preview of {self.selected_file.name}")
            
        except Exception as e:
            logger.error(f"Error previewing file: {e}")
            messagebox.showerror("Preview Error", f"Could not preview file:\n{e}")
    
    def on_process_clicked(self) -> None:
        """
        Handle process button click.
        """
        if not self.selected_file:
            messagebox.showwarning("No File", "Please select a file first")
            return
        
        # Check if project folder is set
        if not self.app_state.has_project_folder():
            messagebox.showerror(
                "No Project Folder",
                "Please select a project folder before processing data"
            )
            return
        
        # Disable process button
        self.process_button.configure(state="disabled")
        
        # Show progress
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        self.progress_label.configure(text="Parsing CSV file...")
        
        # Process in background thread
        def process_thread():
            result = self.parse_and_process_csv()
            self.after(0, lambda: self.handle_process_result(result))
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def parse_and_process_csv(self) -> Tuple[bool, Optional[pd.DataFrame], Optional[str]]:
        """
        Parse CSV file with flexible format detection.
        
        Returns:
            Tuple of (success, dataframe, error_message)
        """
        try:
            # Read the file
            with open(self.selected_file, 'r') as f:
                lines = f.readlines()
            
            # Find the header row (contains date and precipitation columns)
            header_row_idx = None
            date_col = None
            precip_col = None
            precip_unit = 'mm'  # Default to mm
            
            for idx, line in enumerate(lines):
                # Check if this line looks like a header
                if ',' in line:
                    parts = [p.strip().lower() for p in line.split(',')]
                    
                    # Look for date column
                    date_candidates = ['date', 'time', 'datetime', 'day']
                    for i, part in enumerate(parts):
                        if any(dc in part for dc in date_candidates):
                            date_col = i
                            break
                    
                    # Look for precipitation column
                    precip_candidates = ['prcp', 'precip', 'precipitation', 'rain', 'rainfall']
                    for i, part in enumerate(parts):
                        if any(pc in part for pc in precip_candidates):
                            precip_col = i
                            
                            # Check for unit indicators
                            if 'in' in part or 'inch' in part:
                                precip_unit = 'in'
                            elif 'mm' in part or 'millimeter' in part:
                                precip_unit = 'mm'
                            
                            break
                    
                    # If we found both columns, this is the header
                    if date_col is not None and precip_col is not None:
                        header_row_idx = idx
                        break
            
            if header_row_idx is None:
                return False, None, "Could not find date and precipitation columns in CSV file.\n\n" \
                                   "Expected column names like: DATE, PRCP, Precipitation, etc."
            
            # Read the data starting from the header row
            df = pd.read_csv(self.selected_file, skiprows=header_row_idx)
            
            # Get actual column names
            date_col_name = df.columns[date_col]
            precip_col_name = df.columns[precip_col]
            
            logger.info(f"Detected columns: date='{date_col_name}', precip='{precip_col_name}', unit={precip_unit}")
            
            # Rename columns to standard names
            df = df.rename(columns={
                date_col_name: 'DATE',
                precip_col_name: 'PRCP'
            })
            
            # Keep only DATE and PRCP columns
            df = df[['DATE', 'PRCP']]
            
            # Convert DATE to datetime
            df['DATE'] = pd.to_datetime(df['DATE'])
            
            # Convert precipitation to mm if needed
            if precip_unit == 'in':
                logger.info("Converting precipitation from inches to mm")
                df['PRCP'] = df['PRCP'] * 25.4
            
            # Remove rows with missing values
            df = df.dropna()
            
            # Sort by date
            df = df.sort_values('DATE')
            
            logger.info(f"Parsed {len(df)} rows of data from {df['DATE'].min()} to {df['DATE'].max()}")
            
            return True, df, None
            
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}", exc_info=True)
            return False, None, f"Error parsing CSV file:\n\n{str(e)}"
    
    def handle_process_result(self, result: Tuple[bool, Optional[pd.DataFrame], Optional[str]]) -> None:
        """
        Handle CSV processing result.
        
        Args:
            result: Tuple of (success, dataframe, error_message)
        """
        success, df, error = result
        
        if not success:
            self.progress_bar.stop()
            self.progress_bar.set(0)
            self.progress_label.configure(text="Processing failed")
            self.process_button.configure(state="normal")
            messagebox.showerror("Processing Failed", error)
            return
        
        # Store precipitation data in app state so it's available for plotting
        self.app_state.set_precipitation_data(df)
        
        # Update progress
        self.progress_label.configure(text="Calculating parameters...")
        
        # Calculate parameters in background thread
        def calculate_thread():
            calc_result = self.data_controller.calculate_historical_parameters(df)
            # Schedule UI update on main thread
            self.after(0, lambda: self.handle_calculation_result(calc_result))
        
        threading.Thread(target=calculate_thread, daemon=True).start()
    
    def handle_calculation_result(self, result) -> None:
        """
        Handle parameter calculation result.
        
        This runs on the main thread to safely update UI.
        
        Args:
            result: Result object from calculate_historical_parameters()
        """
        # Stop progress
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        
        # Re-enable process button
        self.process_button.configure(state="normal")
        
        if not result.success:
            self.progress_label.configure(text="Calculation failed")
            self.progress_bar.set(0)
            messagebox.showerror(
                "Calculation Failed",
                f"Failed to calculate parameters:\n\n{result.error}"
            )
            return
        
        # Success - update app state on main thread to trigger observers safely
        if result.value:
            logger.info(f"Setting historical params in app_state: {result.value}")
            self.app_state.set_historical_params(result.value)
        else:
            logger.warning("Calculation succeeded but result.value is None")
        
        self.progress_label.configure(text="Processing complete!")
        self.progress_bar.set(1.0)
        messagebox.showinfo(
            "Processing Complete",
            f"Successfully processed {self.selected_file.name}\n\n"
            f"View the calculated parameters in the 'Parameters' tab."
        )
    
    def on_state_change(self, state_key: str, new_value) -> None:
        """
        React to application state changes.
        
        Args:
            state_key: Name of the state property that changed
            new_value: New value of the state property
        """
        pass
    
    def destroy(self) -> None:
        """
        Clean up resources when panel is destroyed.
        """
        self.app_state.unregister_observer(self.on_state_change)
        super().destroy()
