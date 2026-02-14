"""
Trend analysis panel view component for PrecipGen Desktop.

This module provides the UI for analyzing temporal trends in Markov parameters
by season, including reversion rates, volatilities, and trend slopes.
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


class TrendAnalysisPanel(ctk.CTkFrame):
    """
    UI component for seasonal trend analysis of Markov parameters.
    
    Analyzes how Markov parameters (Pww, Pwd, alpha, beta) change over time
    by season, computing reversion rates, volatilities, and trend slopes.
    
    Attributes:
        app_state: Application state manager
        analysis_controller: Controller for trend analysis operations
    """
    
    def __init__(self, parent, app_state: AppState, analysis_controller: AnalysisController):
        """
        Initialize TrendAnalysisPanel.
        
        Args:
            parent: Parent widget (typically MainWindow tab)
            app_state: AppState instance for observing state changes
            analysis_controller: AnalysisController for trend calculations
        """
        super().__init__(parent, corner_radius=0)
        
        self.app_state = app_state
        self.analysis_controller = analysis_controller
        
        # Setup the panel layout
        self.setup_ui()
        
        # Register as observer for state changes
        self.app_state.register_observer(self.on_state_change)
        
        # Display results if already available
        if self.app_state.has_trend_analysis_results():
            self.display_results(self.app_state.trend_analysis_results)
    
    def setup_ui(self) -> None:
        """
        Configure the panel layout and widgets.
        """
        # Configure grid layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Control frame (station selector, year inputs, and calculate button)
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
        
        # Year range frame
        year_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        year_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")
        
        # Start year label and input
        start_year_label = ctk.CTkLabel(
            year_frame,
            text="Start Year:",
            font=ctk.CTkFont(size=12)
        )
        start_year_label.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")
        
        self.start_year_entry = ctk.CTkEntry(
            year_frame,
            width=100,
            placeholder_text="e.g., 1950"
        )
        self.start_year_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # End year label and input
        end_year_label = ctk.CTkLabel(
            year_frame,
            text="End Year:",
            font=ctk.CTkFont(size=12)
        )
        end_year_label.grid(row=0, column=2, padx=(20, 5), pady=5, sticky="w")
        
        self.end_year_entry = ctk.CTkEntry(
            year_frame,
            width=100,
            placeholder_text="e.g., 2023"
        )
        self.end_year_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Calculate button
        self.calculate_button = ctk.CTkButton(
            self.control_frame,
            text="Calculate Trends",
            command=self.on_calculate_clicked,
            state="disabled",
            width=150
        )
        self.calculate_button.grid(row=0, column=2, padx=10, pady=10, sticky="e")
        
        # Progress indicator
        self.progress_bar = ctk.CTkProgressBar(self.control_frame)
        self.progress_bar.grid(row=2, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()  # Hide initially
        
        # Results scrollable frame
        self.results_scrollable = ctk.CTkScrollableFrame(self)
        self.results_scrollable.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.results_scrollable.grid_columnconfigure(0, weight=1)
        
        # Empty state message
        self.empty_state_label = ctk.CTkLabel(
            self.results_scrollable,
            text="No trend analysis results yet.\n\nSelect a station, specify year range, and click 'Calculate Trends' to begin.",
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
            text="Download Trends",
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
        
        Triggers seasonal trend calculation in a background thread.
        """
        station_file = self.station_selector.get()
        
        if not station_file or station_file in ["No stations available", "No working directory selected"]:
            messagebox.showerror(
                "No Station Selected",
                "Please select a station file to analyze."
            )
            return
        
        # Validate year inputs
        try:
            start_year = int(self.start_year_entry.get())
            end_year = int(self.end_year_entry.get())
        except ValueError:
            messagebox.showerror(
                "Invalid Year Range",
                "Please enter valid integer years for both start and end year."
            )
            return
        
        if start_year >= end_year:
            messagebox.showerror(
                "Invalid Year Range",
                "Start year must be less than end year."
            )
            return
        
        logger.info(f"Calculating seasonal trends for {station_file} ({start_year}-{end_year})")
        
        # Disable controls and show progress
        self.calculate_button.configure(state="disabled")
        self.station_selector.configure(state="disabled")
        self.start_year_entry.configure(state="disabled")
        self.end_year_entry.configure(state="disabled")
        self.progress_bar.grid()
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        # Run calculation in background thread
        def calculate_thread():
            result = self.analysis_controller.calculate_seasonal_trends(
                station_file, start_year, end_year
            )
            
            # Handle result on main thread
            self.after(0, lambda: self.handle_calculation_result(result))
        
        threading.Thread(target=calculate_thread, daemon=True).start()
    
    def handle_calculation_result(self, result) -> None:
        """
        Handle calculation result from AnalysisController.
        
        Args:
            result: Result object from calculate_seasonal_trends()
        """
        # Stop and hide progress indicator
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        
        # Re-enable controls
        self.calculate_button.configure(state="normal")
        self.station_selector.configure(state="readonly")
        self.start_year_entry.configure(state="normal")
        self.end_year_entry.configure(state="normal")
        
        if result.success:
            # Results will be displayed via state observer
            logger.info("Seasonal trends calculated successfully")
            messagebox.showinfo(
                "Calculation Complete",
                "Seasonal trends calculated successfully."
            )
        else:
            logger.error(f"Calculation failed: {result.error}")
            error_message = f"{result.error}\n\n"
            error_message += "Troubleshooting:\n"
            error_message += "• Verify the year range is within the data's date range\n"
            error_message += "• Ensure the year range spans at least 10 years for meaningful trends\n"
            error_message += "• Check that the data has sufficient coverage in the specified period\n"
            error_message += "• Try a different year range or station with more complete data"
            messagebox.showerror(
                "Calculation Failed",
                error_message
            )
    
    def display_results(self, results) -> None:
        """
        Display calculated seasonal trend results.
        
        Args:
            results: TrendAnalysisResults object with calculated trends
        """
        try:
            logger.info(f"Displaying trend analysis results for {results.station_file}")
            
            # Hide empty state message
            self.empty_state_label.grid_remove()
            
            # Clear previous results
            for widget in self.results_scrollable.winfo_children():
                if widget != self.empty_state_label:
                    widget.destroy()
            
            # Title
            title_label = ctk.CTkLabel(
                self.results_scrollable,
                text="Seasonal Trend Analysis",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            title_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
            
            # Metadata
            metadata_text = (
                f"Station: {results.station_file} | "
                f"Analysis Period: {results.start_year} to {results.end_year}"
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
                text="Temporal trends in Markov parameters by season.\n"
                     "Shows how precipitation patterns change over time for Winter, Spring, Summer, and Fall.",
                font=ctk.CTkFont(size=11),
                text_color="gray",
                justify="left"
            )
            description_label.grid(row=2, column=0, padx=10, pady=(0, 15), sticky="w")
            
            # View seasonal trends button
            view_button = ctk.CTkButton(
                self.results_scrollable,
                text="View Seasonal Trends",
                command=lambda: self.show_trends_table(results),
                width=200
            )
            view_button.grid(row=3, column=0, padx=10, pady=(0, 20), sticky="w")
            
            # Trend plots section
            self.display_trend_plots(results)
            
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
    
    def display_trend_plots(self, results) -> None:
        """
        Display embedded trend plots for each parameter.
        
        Args:
            results: TrendAnalysisResults object
        """
        # Section title
        plots_title = ctk.CTkLabel(
            self.results_scrollable,
            text="Trend Plots by Parameter",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        plots_title.grid(row=4, column=0, padx=10, pady=(15, 10), sticky="w")
        
        # Create plots for each parameter
        param_names = ['Pww', 'Pwd', 'alpha', 'beta']
        param_labels = {
            'Pww': 'Wet-Wet Transition Probability',
            'Pwd': 'Wet-Dry Transition Probability',
            'alpha': 'Gamma Distribution Alpha',
            'beta': 'Gamma Distribution Beta'
        }
        
        for idx, param in enumerate(param_names):
            # Create button to show plot
            plot_button = ctk.CTkButton(
                self.results_scrollable,
                text=f"View {param} Trends",
                command=lambda p=param, label=param_labels[param]: self.show_trend_plot(results, p, label),
                width=180
            )
            plot_button.grid(row=5+idx, column=0, padx=10, pady=5, sticky="w")
    
    def show_trends_table(self, results) -> None:
        """
        Display seasonal trends table in a new window.
        
        Args:
            results: TrendAnalysisResults object
        """
        # Create new top-level window
        table_window = ctk.CTkToplevel(self)
        table_window.title("Seasonal Trends Table")
        table_window.geometry("900x600")
        
        # Configure grid
        table_window.grid_rowconfigure(1, weight=1)
        table_window.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            table_window,
            text="Seasonal Trends: Reversion Rates, Volatilities, and Slopes",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Create scrollable frame for table
        table_scrollable = ctk.CTkScrollableFrame(table_window)
        table_scrollable.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")
        table_scrollable.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        
        # Headers
        headers = ["Parameter", "Season", "Reversion Rate", "Volatility", "Trend Slope"]
        for col, header in enumerate(headers):
            label = ctk.CTkLabel(
                table_scrollable,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            label.grid(row=0, column=col, padx=10, pady=5, sticky="ew")
        
        # Display trend values
        trends_df = results.seasonal_trends
        for idx, row in trends_df.iterrows():
            row_frame = ctk.CTkFrame(table_scrollable, fg_color="transparent")
            row_frame.grid(row=idx+1, column=0, columnspan=5, sticky="ew", pady=2)
            row_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
            
            # Parameter
            param_label = ctk.CTkLabel(
                row_frame,
                text=row['parameter'],
                font=ctk.CTkFont(size=11)
            )
            param_label.grid(row=0, column=0, padx=10, pady=3)
            
            # Season
            season_label = ctk.CTkLabel(
                row_frame,
                text=row['season'],
                font=ctk.CTkFont(size=11)
            )
            season_label.grid(row=0, column=1, padx=10, pady=3)
            
            # Reversion Rate
            reversion_label = ctk.CTkLabel(
                row_frame,
                text=f"{row['reversion_rate']:.4f}",
                font=ctk.CTkFont(size=11)
            )
            reversion_label.grid(row=0, column=2, padx=10, pady=3)
            
            # Volatility
            volatility_label = ctk.CTkLabel(
                row_frame,
                text=f"{row['volatility']:.4f}",
                font=ctk.CTkFont(size=11)
            )
            volatility_label.grid(row=0, column=3, padx=10, pady=3)
            
            # Trend Slope
            slope_label = ctk.CTkLabel(
                row_frame,
                text=f"{row['trend_slope']:.6f}",
                font=ctk.CTkFont(size=11)
            )
            slope_label.grid(row=0, column=4, padx=10, pady=3)
        
        # Close button
        close_button = ctk.CTkButton(
            table_window,
            text="Close",
            command=table_window.destroy,
            width=100
        )
        close_button.grid(row=2, column=0, pady=(0, 20))
    
    def show_trend_plot(self, results, param_name: str, param_label: str) -> None:
        """
        Display trend plot for a specific parameter in a new window.
        
        Args:
            results: TrendAnalysisResults object
            param_name: Name of parameter ('Pww', 'Pwd', 'alpha', 'beta')
            param_label: Display label for parameter
        """
        # Create new top-level window
        plot_window = ctk.CTkToplevel(self)
        plot_window.title(f"{param_name} Trends by Season")
        plot_window.geometry("900x700")
        
        # Configure grid
        plot_window.grid_rowconfigure(0, weight=1)
        plot_window.grid_columnconfigure(0, weight=1)
        
        try:
            # Get trend data for this parameter
            param_data = results.trend_data[param_name]
            
            # Create figure
            fig = Figure(figsize=(10, 7), dpi=100)
            ax = fig.add_subplot(111)
            
            # Define colors for seasons
            season_colors = {
                'Winter': '#1f77b4',
                'Spring': '#2ca02c',
                'Summer': '#ff7f0e',
                'Fall': '#d62728'
            }
            
            # Plot each season
            for season in ['Winter', 'Spring', 'Summer', 'Fall']:
                if season in param_data.columns:
                    season_data = param_data[season].dropna()
                    if not season_data.empty:
                        ax.plot(
                            season_data.index,
                            season_data.values,
                            marker='o',
                            linestyle='-',
                            linewidth=2,
                            markersize=6,
                            label=season,
                            color=season_colors[season],
                            alpha=0.8
                        )
            
            # Formatting
            ax.set_xlabel('Year', fontsize=12)
            ax.set_ylabel(param_label, fontsize=12)
            ax.set_title(f'{param_label} Trends by Season\n{results.station_file} ({results.start_year}-{results.end_year})',
                        fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='best', fontsize=10)
            
            # Add trend statistics text box
            trends_for_param = results.seasonal_trends[
                results.seasonal_trends['parameter'] == param_name
            ]
            
            stats_text = f"Trend Statistics for {param_name}:\n\n"
            for _, row in trends_for_param.iterrows():
                stats_text += (
                    f"{row['season']}:\n"
                    f"  Slope: {row['trend_slope']:.6f}\n"
                    f"  Volatility: {row['volatility']:.4f}\n"
                    f"  Reversion: {row['reversion_rate']:.4f}\n\n"
                )
            
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                   fontsize=9, verticalalignment='top', horizontalalignment='left',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7),
                   family='monospace')
            
            fig.tight_layout()
            
            # Create canvas
            canvas = FigureCanvasTkAgg(fig, master=plot_window)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            canvas.draw()
            
            # Add close button
            close_button = ctk.CTkButton(
                plot_window,
                text="Close",
                command=plot_window.destroy,
                width=100
            )
            close_button.grid(row=1, column=0, pady=(0, 10))
            
        except Exception as e:
            logger.error(f"Error creating trend plot: {e}", exc_info=True)
            plot_window.destroy()
            messagebox.showerror(
                "Plot Error",
                f"Could not create trend plot:\n{e}"
            )
    
    def on_download_clicked(self) -> None:
        """
        Handle download button click.
        
        Exports seasonal trend analysis results to CSV file with station ID in filename.
        """
        if not self.app_state.has_trend_analysis_results():
            messagebox.showerror(
                "No Results",
                "No trend analysis results available to download."
            )
            return
        
        trends = self.app_state.trend_analysis_results
        
        # Extract station ID from filename (remove extension)
        station_id = Path(trends.station_file).stem
        
        # Create filename with station ID
        output_filename = f"trend_analysis_{station_id}.csv"
        output_path = self.app_state.project_folder / output_filename
        
        logger.info(f"Exporting trend analysis to {output_path}")
        
        # Disable button during export
        self.download_button.configure(state="disabled")
        
        # Run export in background thread
        def export_thread():
            result = self.analysis_controller.export_trend_analysis(trends, output_path)
            
            # Handle result on main thread
            self.after(0, lambda: self.handle_export_result(result))
        
        threading.Thread(target=export_thread, daemon=True).start()
    
    def handle_export_result(self, result) -> None:
        """
        Handle export result from AnalysisController.
        
        Args:
            result: Result object from export_trend_analysis()
        """
        # Re-enable button
        self.download_button.configure(state="normal")
        
        if result.success:
            messagebox.showinfo(
                "Export Successful",
                f"Trend analysis saved to:\n{result.value}"
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
        elif state_key == 'trend_analysis_results' and new_value is not None:
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
