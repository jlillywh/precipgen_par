"""
Markov analysis panel view component for PrecipGen Desktop.

This module provides the UI for calculating and displaying Markov chain
parameters (Pww, Pwd, alpha, beta) for the PrecipGen stochastic simulator.
"""

import logging
import customtkinter as ctk
from pathlib import Path
from typing import Optional
from tkinter import messagebox
import threading

from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.controllers.analysis_controller import AnalysisController


# Configure logging
logger = logging.getLogger(__name__)


class MarkovAnalysisPanel(ctk.CTkFrame):
    """
    UI component for Markov chain parameter calculation.
    
    Calculates monthly transition probabilities (Pww, Pwd) and gamma
    distribution parameters (alpha, beta) for use in PrecipGen simulator.
    
    Attributes:
        app_state: Application state manager
        analysis_controller: Controller for parameter calculations
    """
    
    def __init__(self, parent, app_state: AppState, analysis_controller: AnalysisController):
        """
        Initialize MarkovAnalysisPanel.
        
        Args:
            parent: Parent widget (typically MainWindow tab)
            app_state: AppState instance for observing state changes
            analysis_controller: AnalysisController for parameter calculations
        """
        super().__init__(parent, corner_radius=0)
        
        self.app_state = app_state
        self.analysis_controller = analysis_controller
        
        # Setup the panel layout
        self.setup_ui()
        
        # Register as observer for state changes
        self.app_state.register_observer(self.on_state_change)
        
        # Display results if already available
        if self.app_state.has_markov_parameters():
            self.display_results(self.app_state.markov_parameters)
    
    def setup_ui(self) -> None:
        """
        Configure the panel layout and widgets.
        """
        # Configure grid layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Control frame (station selector and calculate button)
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.control_frame.grid_columnconfigure(1, weight=1)
        
        # Station selector label
        station_label = ctk.CTkLabel(
            self.control_frame,
            text="Select Station:",
            font=ctk.CTkFont(size=12)
        )
        station_label.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        
        # Station selector dropdown
        self.station_selector = ctk.CTkComboBox(
            self.control_frame,
            values=["No stations available"],
            state="readonly",
            command=self.on_station_selected,
            width=300
        )
        self.station_selector.grid(row=0, column=1, padx=5, pady=10, sticky="w")
        self.station_selector.set("No stations available")
        
        # Calculate button
        self.calculate_button = ctk.CTkButton(
            self.control_frame,
            text="Calculate Parameters",
            command=self.on_calculate_clicked,
            state="disabled",
            width=150
        )
        self.calculate_button.grid(row=0, column=2, padx=10, pady=10, sticky="e")
        
        # Progress indicator
        self.progress_bar = ctk.CTkProgressBar(self.control_frame)
        self.progress_bar.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()  # Hide initially
        
        # Results scrollable frame
        self.results_scrollable = ctk.CTkScrollableFrame(self)
        self.results_scrollable.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.results_scrollable.grid_columnconfigure(0, weight=1)
        
        # Empty state message
        self.empty_state_label = ctk.CTkLabel(
            self.results_scrollable,
            text="No Markov parameters calculated yet.\n\nSelect a station and click 'Calculate Parameters' to begin.",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.empty_state_label.grid(row=0, column=0, padx=10, pady=50, sticky="w")
        
        # Download button frame (at bottom)
        self.download_frame = ctk.CTkFrame(self)
        self.download_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.download_frame.grid_columnconfigure(0, weight=1)
        
        # Download button
        self.download_button = ctk.CTkButton(
            self.download_frame,
            text="Download Parameters",
            command=self.on_download_clicked,
            state="disabled",
            width=150
        )
        self.download_button.grid(row=0, column=0, pady=10)
        
        # Update station list if available
        self.update_station_list()
    
    def update_station_list(self) -> None:
        """
        Update the station selector dropdown with available CSV files.
        """
        if not self.app_state.has_project_folder():
            self.station_selector.configure(values=["No working directory selected"])
            self.station_selector.set("No working directory selected")
            self.calculate_button.configure(state="disabled")
            return
        
        # Get list of CSV files in working directory
        working_dir = self.app_state.project_folder
        csv_files = sorted([f.name for f in working_dir.glob("*.csv")])
        
        if not csv_files:
            self.station_selector.configure(values=["No stations available"])
            self.station_selector.set("No stations available")
            self.calculate_button.configure(state="disabled")
        else:
            self.station_selector.configure(values=csv_files)
            # Use selected station from state if available
            if self.app_state.selected_station and self.app_state.selected_station in csv_files:
                self.station_selector.set(self.app_state.selected_station)
            else:
                self.station_selector.set(csv_files[0])
            self.calculate_button.configure(state="normal")
    
    def on_station_selected(self, station_file: str) -> None:
        """
        Handle station selection from dropdown.
        
        Args:
            station_file: Name of the selected station CSV file
        """
        # Enable calculate button if valid station selected
        if station_file and station_file not in ["No stations available", "No working directory selected"]:
            self.calculate_button.configure(state="normal")
            self.app_state.set_selected_station(station_file)
        else:
            self.calculate_button.configure(state="disabled")
    
    def on_calculate_clicked(self) -> None:
        """
        Handle calculate button click.
        
        Triggers Markov parameter calculation in a background thread.
        """
        station_file = self.station_selector.get()
        
        if not station_file or station_file in ["No stations available", "No working directory selected"]:
            messagebox.showerror(
                "No Station Selected",
                "Please select a station file to analyze."
            )
            return
        
        logger.info(f"Calculating Markov parameters for {station_file}")
        
        # Disable controls and show progress
        self.calculate_button.configure(state="disabled")
        self.station_selector.configure(state="disabled")
        self.progress_bar.grid()
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        # Run calculation in background thread
        def calculate_thread():
            result = self.analysis_controller.calculate_markov_parameters(station_file)
            
            # Handle result on main thread
            self.after(0, lambda: self.handle_calculation_result(result))
        
        threading.Thread(target=calculate_thread, daemon=True).start()
    
    def handle_calculation_result(self, result) -> None:
        """
        Handle calculation result from AnalysisController.
        
        Args:
            result: Result object from calculate_markov_parameters()
        """
        # Stop and hide progress indicator
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        
        # Re-enable controls
        self.calculate_button.configure(state="normal")
        self.station_selector.configure(state="readonly")
        
        if result.success:
            # Results will be displayed via state observer
            logger.info("Markov parameters calculated successfully")
            messagebox.showinfo(
                "Calculation Complete",
                "Markov parameters calculated successfully."
            )
        else:
            logger.error(f"Calculation failed: {result.error}")
            error_message = f"{result.error}\n\n"
            error_message += "Troubleshooting:\n"
            error_message += "• Ensure the CSV file contains valid precipitation data\n"
            error_message += "• Check that the file has sufficient data (at least 1 year)\n"
            error_message += "• Verify the data has enough wet days for parameter estimation\n"
            error_message += "• Try using a station with more complete data coverage"
            messagebox.showerror(
                "Calculation Failed",
                error_message
            )
    
    def display_results(self, results) -> None:
        """
        Display calculated Markov parameters.
        
        Args:
            results: MarkovParameters object with calculated values
        """
        try:
            logger.info(f"Displaying Markov parameters for {results.station_file}")
            
            # Hide empty state message
            self.empty_state_label.grid_remove()
            
            # Clear previous results
            for widget in self.results_scrollable.winfo_children():
                if widget != self.empty_state_label:
                    widget.destroy()
            
            # Title
            title_label = ctk.CTkLabel(
                self.results_scrollable,
                text="Markov Chain Parameters",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            title_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
            
            # Metadata
            metadata_text = (
                f"Station: {results.source_station} | "
                f"Data Range: {results.date_range[0]} to {results.date_range[1]} | "
                f"Calculated: {results.calculation_date.strftime('%Y-%m-%d %H:%M')}"
            )
            metadata_label = ctk.CTkLabel(
                self.results_scrollable,
                text=metadata_text,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            metadata_label.grid(row=1, column=0, padx=10, pady=(0, 20), sticky="w")
            
            # Description
            description_label = ctk.CTkLabel(
                self.results_scrollable,
                text="Monthly Markov chain parameters for PrecipGen stochastic simulator.\n"
                     "Pww: Probability of wet day following wet day | Pwd: Probability of wet day following dry day\n"
                     "alpha, beta: Gamma distribution shape and scale parameters for precipitation amounts",
                font=ctk.CTkFont(size=11),
                text_color="gray",
                justify="left"
            )
            description_label.grid(row=2, column=0, padx=10, pady=(0, 15), sticky="w")
            
            # View parameters button
            view_button = ctk.CTkButton(
                self.results_scrollable,
                text="View Monthly Parameters",
                command=lambda: self.show_parameters_table(results),
                width=200
            )
            view_button.grid(row=3, column=0, padx=10, pady=(0, 20), sticky="w")
            
            # Summary statistics
            self.display_parameter_summary(results)
            
            # Enable download button
            self.download_button.configure(state="normal")
            
            logger.info("Parameters displayed successfully")
            
        except Exception as e:
            logger.error(f"Error displaying results: {e}", exc_info=True)
            error_label = ctk.CTkLabel(
                self.results_scrollable,
                text=f"Error displaying results: {str(e)}",
                font=ctk.CTkFont(size=12),
                text_color="red"
            )
            error_label.grid(row=0, column=0, padx=20, pady=20)
    
    def display_parameter_summary(self, results) -> None:
        """
        Display summary statistics for parameters.
        
        Args:
            results: MarkovParameters object
        """
        # Section title
        summary_title = ctk.CTkLabel(
            self.results_scrollable,
            text="Parameter Summary",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        summary_title.grid(row=4, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Create summary frame
        summary_frame = ctk.CTkFrame(self.results_scrollable)
        summary_frame.grid(row=5, column=0, padx=10, pady=(5, 10), sticky="ew")
        summary_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Calculate summary statistics
        params_df = results.monthly_params
        
        summaries = [
            ("Pww Range", f"{params_df['Pww'].min():.3f} - {params_df['Pww'].max():.3f}"),
            ("Pwd Range", f"{params_df['Pwd'].min():.3f} - {params_df['Pwd'].max():.3f}"),
            ("Alpha Range", f"{params_df['alpha'].min():.3f} - {params_df['alpha'].max():.3f}"),
            ("Beta Range", f"{params_df['beta'].min():.3f} - {params_df['beta'].max():.3f}")
        ]
        
        for col, (label, value) in enumerate(summaries):
            summary_item = ctk.CTkFrame(summary_frame, fg_color="transparent")
            summary_item.grid(row=0, column=col, padx=5, pady=10)
            
            label_widget = ctk.CTkLabel(
                summary_item,
                text=label,
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            label_widget.pack()
            
            value_widget = ctk.CTkLabel(
                summary_item,
                text=value,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            value_widget.pack()
    
    def show_parameters_table(self, results) -> None:
        """
        Display monthly parameters table in a new window.
        
        Args:
            results: MarkovParameters object
        """
        # Create new top-level window
        table_window = ctk.CTkToplevel(self)
        table_window.title("Monthly Markov Parameters")
        table_window.geometry("700x500")
        
        # Configure grid
        table_window.grid_rowconfigure(1, weight=1)
        table_window.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            table_window,
            text="Monthly Markov Chain Parameters",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Create scrollable frame for table
        table_scrollable = ctk.CTkScrollableFrame(table_window)
        table_scrollable.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")
        table_scrollable.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        
        # Headers
        headers = ["Month", "Pww", "Pwd", "Alpha", "Beta"]
        for col, header in enumerate(headers):
            label = ctk.CTkLabel(
                table_scrollable,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            label.grid(row=0, column=col, padx=10, pady=5, sticky="ew")
        
        # Month names
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        # Display parameter values
        params_df = results.monthly_params
        for idx, row in params_df.iterrows():
            row_frame = ctk.CTkFrame(table_scrollable, fg_color="transparent")
            row_frame.grid(row=idx+1, column=0, columnspan=5, sticky="ew", pady=2)
            row_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
            
            # Month name
            month_label = ctk.CTkLabel(
                row_frame,
                text=month_names[int(row['month'])-1],
                font=ctk.CTkFont(size=11)
            )
            month_label.grid(row=0, column=0, padx=10, pady=3)
            
            # Pww
            pww_label = ctk.CTkLabel(
                row_frame,
                text=f"{row['Pww']:.4f}",
                font=ctk.CTkFont(size=11)
            )
            pww_label.grid(row=0, column=1, padx=10, pady=3)
            
            # Pwd
            pwd_label = ctk.CTkLabel(
                row_frame,
                text=f"{row['Pwd']:.4f}",
                font=ctk.CTkFont(size=11)
            )
            pwd_label.grid(row=0, column=2, padx=10, pady=3)
            
            # Alpha
            alpha_label = ctk.CTkLabel(
                row_frame,
                text=f"{row['alpha']:.4f}",
                font=ctk.CTkFont(size=11)
            )
            alpha_label.grid(row=0, column=3, padx=10, pady=3)
            
            # Beta
            beta_label = ctk.CTkLabel(
                row_frame,
                text=f"{row['beta']:.4f}",
                font=ctk.CTkFont(size=11)
            )
            beta_label.grid(row=0, column=4, padx=10, pady=3)
        
        # Close button
        close_button = ctk.CTkButton(
            table_window,
            text="Close",
            command=table_window.destroy,
            width=100
        )
        close_button.grid(row=2, column=0, pady=(0, 20))
    
    def on_download_clicked(self) -> None:
        """
        Handle download button click.
        
        Exports Markov parameters to CSV file in PrecipGen simulator format with station ID in filename.
        """
        if not self.app_state.has_markov_parameters():
            messagebox.showerror(
                "No Parameters",
                "No Markov parameters available to download."
            )
            return
        
        params = self.app_state.markov_parameters
        
        # Extract station ID from filename (remove extension)
        station_id = Path(params.station_file).stem
        
        # Create filename with station ID
        output_filename = f"markov_params_{station_id}.csv"
        output_path = self.app_state.project_folder / output_filename
        
        logger.info(f"Exporting Markov parameters to {output_path}")
        
        # Disable button during export
        self.download_button.configure(state="disabled")
        
        # Run export in background thread
        def export_thread():
            result = self.analysis_controller.export_markov_parameters(params, output_path)
            
            # Handle result on main thread
            self.after(0, lambda: self.handle_export_result(result))
        
        threading.Thread(target=export_thread, daemon=True).start()
    
    def handle_export_result(self, result) -> None:
        """
        Handle export result from AnalysisController.
        
        Args:
            result: Result object from export_markov_parameters()
        """
        # Re-enable button
        self.download_button.configure(state="normal")
        
        if result.success:
            messagebox.showinfo(
                "Export Successful",
                f"Parameters saved to:\n{result.value}\n\n"
                f"This file is formatted for use with the PrecipGen simulator."
            )
        else:
            error_message = f"{result.error}\n\n"
            error_message += "Troubleshooting:\n"
            error_message += "• Check that you have write permissions to the working directory\n"
            error_message += "• Ensure the file is not open in another program\n"
            error_message += "• Verify you have sufficient disk space\n"
            error_message += "• Try closing any programs that might be using the file"
            messagebox.showerror(
                "Export Failed",
                error_message
            )
    
    def on_state_change(self, state_key: str, new_value) -> None:
        """
        React to application state changes.
        
        Args:
            state_key: Name of the state property that changed
            new_value: New value of the state property
        """
        if state_key == 'project_folder':
            self.update_station_list()
        elif state_key == 'available_stations':
            self.update_station_list()
        elif state_key == 'selected_station':
            self.update_station_list()
        elif state_key == 'markov_parameters' and new_value is not None:
            self.display_results(new_value)
    
    def destroy(self) -> None:
        """
        Clean up resources when panel is destroyed.
        
        Unregisters the state observer before destroying the widget.
        """
        # Unregister observer
        self.app_state.unregister_observer(self.on_state_change)
        
        # Call parent destroy
        super().destroy()
