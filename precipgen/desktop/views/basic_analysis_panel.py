"""
Basic analysis panel view component for PrecipGen Desktop.

This module provides the UI for displaying descriptive statistics and
data quality metrics for precipitation time series.
"""

import logging
import customtkinter as ctk
from pathlib import Path
from typing import Optional
from tkinter import messagebox
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.controllers.analysis_controller import AnalysisController


# Configure logging
logger = logging.getLogger(__name__)


class BasicAnalysisPanel(ctk.CTkFrame):
    """
    UI component for basic descriptive statistics analysis.
    
    Displays comprehensive statistics including date range, gap analysis,
    annual precipitation statistics, monthly statistics, and extreme values.
    
    Attributes:
        app_state: Application state manager
        analysis_controller: Controller for statistical analysis operations
    """
    
    def __init__(self, parent, app_state: AppState, analysis_controller: AnalysisController):
        """
        Initialize BasicAnalysisPanel.
        
        Args:
            parent: Parent widget (typically MainWindow tab)
            app_state: AppState instance for observing state changes
            analysis_controller: AnalysisController for statistical calculations
        """
        super().__init__(parent, corner_radius=0)
        
        self.app_state = app_state
        self.analysis_controller = analysis_controller
        
        # Setup the panel layout
        self.setup_ui()
        
        # Register as observer for state changes
        self.app_state.register_observer(self.on_state_change)
        
        # Display results if already available
        if self.app_state.has_basic_analysis_results():
            self.display_results(self.app_state.basic_analysis_results)
    
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
            text="Calculate",
            command=self.on_calculate_clicked,
            state="disabled",
            width=120
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
            text="No analysis results yet.\n\nSelect a station and click 'Calculate' to begin.",
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
            text="Download Results",
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
        
        Triggers basic statistics calculation in a background thread.
        """
        station_file = self.station_selector.get()
        
        if not station_file or station_file in ["No stations available", "No working directory selected"]:
            messagebox.showerror(
                "No Station Selected",
                "Please select a station file to analyze."
            )
            return
        
        logger.info(f"Calculating basic statistics for {station_file}")
        
        # Disable controls and show progress
        self.calculate_button.configure(state="disabled")
        self.station_selector.configure(state="disabled")
        self.progress_bar.grid()
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        # Run calculation in background thread
        def calculate_thread():
            result = self.analysis_controller.calculate_basic_stats(station_file)
            
            # Handle result on main thread
            self.after(0, lambda: self.handle_calculation_result(result))
        
        threading.Thread(target=calculate_thread, daemon=True).start()
    
    def handle_calculation_result(self, result) -> None:
        """
        Handle calculation result from AnalysisController.
        
        Args:
            result: Result object from calculate_basic_stats()
        """
        # Stop and hide progress indicator
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        
        # Re-enable controls
        self.calculate_button.configure(state="normal")
        self.station_selector.configure(state="readonly")
        
        if result.success:
            # Results will be displayed via state observer
            logger.info("Basic statistics calculated successfully")
            messagebox.showinfo(
                "Calculation Complete",
                "Basic statistics calculated successfully."
            )
        else:
            logger.error(f"Calculation failed: {result.error}")
            error_message = f"{result.error}\n\n"
            error_message += "Troubleshooting:\n"
            error_message += "• Ensure the CSV file contains valid date and precipitation data\n"
            error_message += "• Check that the file has at least 1 year of data\n"
            error_message += "• Verify the file is not corrupted or empty\n"
            error_message += "• Try re-downloading or re-importing the station data"
            messagebox.showerror(
                "Calculation Failed",
                error_message
            )
    
    def display_results(self, results) -> None:
        """
        Display calculated basic analysis results.
        
        Args:
            results: BasicAnalysisResults object with calculated statistics
        """
        try:
            logger.info(f"Displaying basic analysis results for {results.station_file}")
            
            # Hide empty state message
            self.empty_state_label.grid_remove()
            
            # Clear previous results
            for widget in self.results_scrollable.winfo_children():
                if widget != self.empty_state_label:
                    widget.destroy()
            
            # Title
            title_label = ctk.CTkLabel(
                self.results_scrollable,
                text="Basic Analysis Results",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            title_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
            
            # Metadata
            metadata_text = (
                f"Station: {results.station_file} | "
                f"Data Range: {results.date_range[0]} to {results.date_range[1]} | "
                f"Years on Record: {results.years_on_record}"
            )
            metadata_label = ctk.CTkLabel(
                self.results_scrollable,
                text=metadata_text,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            metadata_label.grid(row=1, column=0, padx=10, pady=(0, 20), sticky="w")
            
            # Data Quality Section
            self.display_data_quality(results)
            
            # Annual Statistics Section
            self.display_annual_statistics(results)
            
            # Monthly Statistics Section
            self.display_monthly_statistics(results)
            
            # Extreme Values Section
            self.display_extreme_values(results)
            
            # Enable download button
            self.download_button.configure(state="normal")
            
            logger.info("Results displayed successfully")
            
        except Exception as e:
            logger.error(f"Error displaying results: {e}", exc_info=True)
            error_label = ctk.CTkLabel(
                self.results_scrollable,
                text=f"Error displaying results: {str(e)}",
                font=ctk.CTkFont(size=12),
                text_color="red"
            )
            error_label.grid(row=0, column=0, padx=20, pady=20)
    
    def display_data_quality(self, results) -> None:
        """
        Display data quality metrics including gap analysis.
        
        Args:
            results: BasicAnalysisResults object
        """
        # Section title
        quality_title = ctk.CTkLabel(
            self.results_scrollable,
            text="Data Quality",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        quality_title.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Create summary frame
        summary_frame = ctk.CTkFrame(self.results_scrollable)
        summary_frame.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")
        summary_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Summary metrics
        gap_analysis = results.gap_analysis
        metrics = [
            ("Data Coverage", f"{gap_analysis['coverage_pct']}%"),
            ("Missing Days", str(gap_analysis['missing_days'])),
            ("Short Gaps (≤7d)", str(gap_analysis['short_gaps'])),
            ("Long Gaps (>7d)", str(gap_analysis['long_gaps']))
        ]
        
        for col, (label, value) in enumerate(metrics):
            metric_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
            metric_frame.grid(row=0, column=col, padx=5, pady=10)
            
            label_widget = ctk.CTkLabel(
                metric_frame,
                text=label,
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            label_widget.pack()
            
            value_widget = ctk.CTkLabel(
                metric_frame,
                text=value,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            value_widget.pack()
    
    def display_annual_statistics(self, results) -> None:
        """
        Display annual precipitation statistics and histogram.
        
        Args:
            results: BasicAnalysisResults object
        """
        # Section title
        annual_title = ctk.CTkLabel(
            self.results_scrollable,
            text="Annual Precipitation",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        annual_title.grid(row=4, column=0, padx=10, pady=(15, 5), sticky="w")
        
        # Statistics frame
        stats_frame = ctk.CTkFrame(self.results_scrollable)
        stats_frame.grid(row=5, column=0, padx=10, pady=(5, 10), sticky="ew")
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Statistics
        stats = [
            ("Mean Annual", f"{results.mean_annual:.1f} mm"),
            ("Std Deviation", f"{results.std_annual:.1f} mm"),
            ("Best Fit Distribution", results.best_fit_distribution)
        ]
        
        for col, (label, value) in enumerate(stats):
            stat_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            stat_frame.grid(row=0, column=col, padx=5, pady=10)
            
            label_widget = ctk.CTkLabel(
                stat_frame,
                text=label,
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            label_widget.pack()
            
            value_widget = ctk.CTkLabel(
                stat_frame,
                text=value,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            value_widget.pack()
        
        # Histogram button
        histogram_button = ctk.CTkButton(
            self.results_scrollable,
            text="View Annual Histogram",
            command=lambda: self.show_histogram(results),
            width=180
        )
        histogram_button.grid(row=6, column=0, padx=10, pady=(0, 10), sticky="w")
    
    def display_monthly_statistics(self, results) -> None:
        """
        Display button to view monthly statistics in a dialog.
        
        Args:
            results: BasicAnalysisResults object
        """
        # Section title
        monthly_title = ctk.CTkLabel(
            self.results_scrollable,
            text="Monthly Statistics",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        monthly_title.grid(row=7, column=0, padx=10, pady=(15, 5), sticky="w")
        
        # Store results for dialog
        self.current_monthly_stats = results.monthly_stats
        
        # Button to view monthly statistics
        view_button = ctk.CTkButton(
            self.results_scrollable,
            text="View Monthly Statistics",
            command=self.show_monthly_statistics_dialog,
            width=200
        )
        view_button.grid(row=8, column=0, padx=10, pady=(5, 10), sticky="w")
    
    def display_extreme_values(self, results) -> None:
        """
        Display extreme value statistics.
        
        Args:
            results: BasicAnalysisResults object
        """
        # Section title
        extreme_title = ctk.CTkLabel(
            self.results_scrollable,
            text="Extreme Values",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        extreme_title.grid(row=9, column=0, padx=10, pady=(15, 5), sticky="w")
        
        # Extremes frame
        extremes_frame = ctk.CTkFrame(self.results_scrollable)
        extremes_frame.grid(row=10, column=0, padx=10, pady=(5, 10), sticky="ew")
        extremes_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Extreme values
        extremes = [
            ("Peak 1-Day Rainfall", f"{results.peak_1day:.1f} mm"),
            ("Max Consecutive Dry Days", f"{results.max_consecutive_dry:.0f} days"),
            ("Max Consecutive Wet Days", f"{results.max_consecutive_wet:.0f} days")
        ]
        
        for col, (label, value) in enumerate(extremes):
            extreme_frame = ctk.CTkFrame(extremes_frame, fg_color="transparent")
            extreme_frame.grid(row=0, column=col, padx=5, pady=10)
            
            label_widget = ctk.CTkLabel(
                extreme_frame,
                text=label,
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            label_widget.pack()
            
            value_widget = ctk.CTkLabel(
                extreme_frame,
                text=value,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            value_widget.pack()
    
    def show_histogram(self, results) -> None:
        """
        Display annual precipitation histogram in a new window.
        
        Args:
            results: BasicAnalysisResults object
        """
        # Create new top-level window
        histogram_window = ctk.CTkToplevel(self)
        histogram_window.title("Annual Precipitation Histogram")
        histogram_window.geometry("800x600")
        
        # Configure grid
        histogram_window.grid_rowconfigure(0, weight=1)
        histogram_window.grid_columnconfigure(0, weight=1)
        
        try:
            # Create figure
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            # Plot histogram
            annual_totals = results.annual_totals.values
            ax.hist(annual_totals, bins=20, color='#1f77b4', alpha=0.7, edgecolor='black')
            
            # Add mean line
            mean_val = results.mean_annual
            ax.axvline(x=mean_val, color='red', linestyle='--', linewidth=2,
                      label=f'Mean: {mean_val:.1f} mm')
            
            # Formatting
            ax.set_xlabel('Annual Precipitation (mm)', fontsize=12)
            ax.set_ylabel('Frequency', fontsize=12)
            ax.set_title('Distribution of Annual Precipitation Totals', 
                        fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            ax.legend(loc='best')
            
            # Add statistics text box
            stats_text = (
                f"Mean: {mean_val:.1f} mm\n"
                f"Std Dev: {results.std_annual:.1f} mm\n"
                f"Min: {annual_totals.min():.1f} mm\n"
                f"Max: {annual_totals.max():.1f} mm\n"
                f"Distribution: {results.best_fit_distribution}"
            )
            ax.text(0.98, 0.98, stats_text, transform=ax.transAxes,
                   fontsize=10, verticalalignment='top', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            fig.tight_layout()
            
            # Create canvas
            canvas = FigureCanvasTkAgg(fig, master=histogram_window)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            canvas.draw()
            
            # Add close button
            close_button = ctk.CTkButton(
                histogram_window,
                text="Close",
                command=histogram_window.destroy,
                width=100
            )
            close_button.grid(row=1, column=0, pady=(0, 10))
            
        except Exception as e:
            logger.error(f"Error creating histogram: {e}", exc_info=True)
            histogram_window.destroy()
            messagebox.showerror(
                "Plot Error",
                f"Could not create histogram:\n{e}"
            )
    
    def show_monthly_statistics_dialog(self) -> None:
        """
        Display monthly statistics in a dialog window.
        """
        if not hasattr(self, 'current_monthly_stats') or self.current_monthly_stats is None:
            messagebox.showerror(
                "No Data",
                "No monthly statistics available to display."
            )
            return
        
        # Create new top-level window
        dialog = ctk.CTkToplevel(self)
        dialog.title("Monthly Statistics")
        dialog.geometry("500x500")
        
        # Configure grid
        dialog.grid_rowconfigure(0, weight=1)
        dialog.grid_columnconfigure(0, weight=1)
        
        # Create scrollable frame
        scrollable = ctk.CTkScrollableFrame(dialog)
        scrollable.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollable.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            scrollable,
            text="Monthly Precipitation Statistics",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 15))
        
        # Headers
        headers = ["Month", "Mean (mm)", "Std Dev (mm)"]
        for col, header in enumerate(headers):
            label = ctk.CTkLabel(
                scrollable,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            label.grid(row=1, column=col, padx=10, pady=5, sticky="ew")
        
        # Month names
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        # Display monthly values
        for idx, row in self.current_monthly_stats.iterrows():
            # Alternate row colors for readability
            bg_color = ("gray85", "gray70") if idx % 2 == 0 else ("gray90", "gray75")
            
            row_frame = ctk.CTkFrame(scrollable, fg_color=bg_color)
            row_frame.grid(row=idx+2, column=0, columnspan=3, sticky="ew", padx=5, pady=1)
            row_frame.grid_columnconfigure((0, 1, 2), weight=1)
            
            month_label = ctk.CTkLabel(
                row_frame,
                text=month_names[int(row['month'])-1],
                font=ctk.CTkFont(size=11)
            )
            month_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            mean_label = ctk.CTkLabel(
                row_frame,
                text=f"{row['mean']:.1f}",
                font=ctk.CTkFont(size=11)
            )
            mean_label.grid(row=0, column=1, padx=10, pady=5)
            
            std_label = ctk.CTkLabel(
                row_frame,
                text=f"{row['std']:.1f}",
                font=ctk.CTkFont(size=11)
            )
            std_label.grid(row=0, column=2, padx=10, pady=5)
        
        # Close button
        close_button = ctk.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            width=100
        )
        close_button.grid(row=1, column=0, pady=(0, 10))
    
    def on_download_clicked(self) -> None:
        """
        Handle download button click.
        
        Exports basic analysis results to CSV file with station ID in filename.
        """
        if not self.app_state.has_basic_analysis_results():
            messagebox.showerror(
                "No Results",
                "No analysis results available to download."
            )
            return
        
        results = self.app_state.basic_analysis_results
        
        # Extract station ID from filename (remove extension)
        station_id = Path(results.station_file).stem
        
        # Create filename with station ID
        output_filename = f"basic_stats_{station_id}.csv"
        output_path = self.app_state.project_folder / output_filename
        
        logger.info(f"Exporting basic statistics to {output_path}")
        
        # Disable button during export
        self.download_button.configure(state="disabled")
        
        # Run export in background thread
        def export_thread():
            result = self.analysis_controller.export_basic_stats(results, output_path)
            
            # Handle result on main thread
            self.after(0, lambda: self.handle_export_result(result))
        
        threading.Thread(target=export_thread, daemon=True).start()
    
    def handle_export_result(self, result) -> None:
        """
        Handle export result from AnalysisController.
        
        Args:
            result: Result object from export_basic_stats()
        """
        # Re-enable button
        self.download_button.configure(state="normal")
        
        if result.success:
            messagebox.showinfo(
                "Export Successful",
                f"Results saved to:\n{result.value}"
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
        elif state_key == 'basic_analysis_results' and new_value is not None:
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
