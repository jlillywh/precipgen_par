"""
Parameters panel view component for PrecipGen Desktop.

This module provides the UI for viewing calculated historical parameters
and data quality metrics.
"""

import logging
import customtkinter as ctk
import threading
import pandas as pd
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.controllers.calibration_controller import CalibrationController
from precipgen.data.gap_analyzer import analyze_gaps, analyze_yearly_gaps


# Configure logging
logger = logging.getLogger(__name__)


class ParametersPanel(ctk.CTkFrame):
    """
    UI component for viewing calculated parameters.
    
    Displays monthly parameters (PWW, PWD, Alpha, Beta) and
    random walk parameters (volatility and reversion rates).
    
    Attributes:
        app_state: Application state manager
        calibration_controller: Controller for parameter export
    """
    
    def __init__(self, parent, app_state: AppState, calibration_controller: CalibrationController):
        """
        Initialize ParametersPanel.
        
        Args:
            parent: Parent widget (typically MainWindow tab)
            app_state: AppState instance for observing state changes
            calibration_controller: CalibrationController for export functionality
        """
        super().__init__(parent, corner_radius=0)
        
        self.app_state = app_state
        self.calibration_controller = calibration_controller
        
        # Setup the panel layout
        self.setup_ui()
        
        # Register as observer for state changes
        self.app_state.register_observer(self.on_state_change)
        
        # Display parameters if already available
        if self.app_state.has_historical_params():
            self.display_historical_parameters(self.app_state.historical_params)
    
    def setup_ui(self) -> None:
        """
        Configure the panel layout and widgets.
        """
        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create scrollable frame for parameters
        self.params_scrollable = ctk.CTkScrollableFrame(self)
        self.params_scrollable.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.params_scrollable.grid_columnconfigure(0, weight=1)
        
        # Status label (shown when no parameters calculated)
        self.params_status_label = ctk.CTkLabel(
            self.params_scrollable,
            text="No parameters calculated yet.\n\nGo to the 'Search' tab to download station data.",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.params_status_label.grid(row=0, column=0, padx=10, pady=50, sticky="w")
        
        # Export button frame (at bottom)
        self.export_frame = ctk.CTkFrame(self)
        self.export_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.export_frame.grid_columnconfigure((0, 1), weight=1)
        
        # View plot button
        self.plot_button = ctk.CTkButton(
            self.export_frame,
            text="View Data Plot",
            command=self.on_plot_clicked,
            state="disabled"
        )
        self.plot_button.grid(row=0, column=0, padx=10, pady=10)
        
        # Export button
        self.export_button = ctk.CTkButton(
            self.export_frame,
            text="Export Parameters",
            command=self.on_export_clicked,
            state="disabled"
        )
        self.export_button.grid(row=0, column=1, padx=10, pady=10)
        
        # Export progress indicator
        self.export_progress = ctk.CTkProgressBar(self.export_frame)
        self.export_progress.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        self.export_progress.set(0)
        self.export_progress.grid_remove()  # Hide initially
    
    def display_historical_parameters(self, params) -> None:
        """
        Display calculated historical parameters.
        
        Shows monthly parameters and random walk parameters in formatted tables.
        
        Args:
            params: HistoricalParameters object with calculated values
        """
        try:
            logger.info(f"display_historical_parameters called with params: {params}")
            
            if params is None:
                logger.warning("display_historical_parameters called with None params")
                return
            
            # Hide status label
            self.params_status_label.grid_remove()
            
            # Clear previous parameter display
            for widget in self.params_scrollable.winfo_children():
                if widget != self.params_status_label:
                    widget.destroy()
            
            logger.info("Creating title label...")
            
            # Title
            title_label = ctk.CTkLabel(
                self.params_scrollable,
                text="Calculated Parameters",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            title_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
            
            logger.info("Creating metadata...")
            
            # Metadata
            metadata_frame = ctk.CTkFrame(self.params_scrollable, fg_color="transparent")
            metadata_frame.grid(row=1, column=0, padx=10, pady=(5, 20), sticky="ew")
            
            metadata_text = (
                f"Station: {params.source_station} | "
                f"Data Range: {params.date_range[0]} to {params.date_range[1]} | "
                f"Calculated: {params.calculation_date.strftime('%Y-%m-%d %H:%M')}"
            )
            
            metadata_label = ctk.CTkLabel(
                metadata_frame,
                text=metadata_text,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            metadata_label.grid(row=0, column=0, padx=0, pady=0, sticky="w")
            
            logger.info("Metadata created successfully")
            
            # Data Quality Section (collapsible)
            self.display_data_quality(params)
            
            # Monthly Parameters Section
            monthly_title = ctk.CTkLabel(
                self.params_scrollable,
                text="Monthly Parameters",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            monthly_title.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")
            
            # Create header row for monthly parameters
            header_frame = ctk.CTkFrame(self.params_scrollable)
            header_frame.grid(row=3, column=0, padx=10, pady=(5, 0), sticky="ew")
            header_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
            
            headers = ["Month", "P(W|W)", "P(W|D)", "α (Alpha)", "β (Beta)"]
            for col, header in enumerate(headers):
                label = ctk.CTkLabel(
                    header_frame,
                    text=header,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    height=20
                )
                label.grid(row=0, column=col, padx=3, pady=2)
            
            # Month names
            month_names = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            
            # Display parameter values for each month
            for month_idx in range(12):
                row_frame = ctk.CTkFrame(self.params_scrollable)
                row_frame.grid(row=4 + month_idx, column=0, padx=10, pady=0, sticky="ew")
                row_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
                
                # Month name
                month_label = ctk.CTkLabel(
                    row_frame,
                    text=month_names[month_idx],
                    font=ctk.CTkFont(size=10),
                    height=18
                )
                month_label.grid(row=0, column=0, padx=3, pady=1)
                
                # Extract values for this month (month_idx is 0-based, but DataFrame index is 1-based)
                month_num = month_idx + 1
                
                # P(W|W)
                pww_val = params.p_wet_wet.loc[month_num, 'PWW'] if month_num in params.p_wet_wet.index else 0.0
                pww_label = ctk.CTkLabel(
                    row_frame,
                    text=f"{pww_val:.3f}",
                    font=ctk.CTkFont(size=10),
                    height=18
                )
                pww_label.grid(row=0, column=1, padx=3, pady=1)
                
                # P(W|D)
                pwd_val = params.p_wet_dry.loc[month_num, 'PWD'] if month_num in params.p_wet_dry.index else 0.0
                pwd_label = ctk.CTkLabel(
                    row_frame,
                    text=f"{pwd_val:.3f}",
                    font=ctk.CTkFont(size=10),
                    height=18
                )
                pwd_label.grid(row=0, column=2, padx=3, pady=1)
                
                # Alpha
                alpha_val = params.alpha.loc[month_num, 'ALPHA'] if month_num in params.alpha.index else 0.0
                alpha_label = ctk.CTkLabel(
                    row_frame,
                    text=f"{alpha_val:.3f}",
                    font=ctk.CTkFont(size=10),
                    height=18
                )
                alpha_label.grid(row=0, column=3, padx=3, pady=1)
                
                # Beta
                beta_val = params.beta.loc[month_num, 'BETA'] if month_num in params.beta.index else 0.0
                beta_label = ctk.CTkLabel(
                    row_frame,
                    text=f"{beta_val:.3f}",
                    font=ctk.CTkFont(size=10),
                    height=18
                )
                beta_label.grid(row=0, column=4, padx=3, pady=1)
            
            # Random Walk Parameters Section (if available)
            if params.volatilities and params.reversion_rates:
                # Title for random walk section
                rw_title = ctk.CTkLabel(
                    self.params_scrollable,
                    text="Random Walk Parameters (Annual)",
                    font=ctk.CTkFont(size=16, weight="bold")
                )
                rw_title.grid(row=16, column=0, padx=10, pady=(15, 5), sticky="w")
                
                # Create table for random walk parameters
                rw_table_frame = ctk.CTkFrame(self.params_scrollable)
                rw_table_frame.grid(row=17, column=0, padx=10, pady=(5, 0), sticky="ew")
                rw_table_frame.grid_columnconfigure((0, 1, 2), weight=1)
                
                # Headers
                rw_headers = ["Parameter", "Volatility (σ)", "Reversion Rate (r)"]
                for col, header in enumerate(rw_headers):
                    label = ctk.CTkLabel(
                        rw_table_frame,
                        text=header,
                        font=ctk.CTkFont(size=11, weight="bold"),
                        height=20
                    )
                    label.grid(row=0, column=col, padx=8, pady=2)
                
                # Display values for each parameter
                param_names = {
                    'PWW': 'P(W|W)',
                    'PWD': 'P(W|D)',
                    'alpha': 'α (Alpha)',
                    'beta': 'β (Beta)'
                }
                
                row_idx = 1
                for param_key, param_display in param_names.items():
                    if param_key in params.volatilities and param_key in params.reversion_rates:
                        # Create row frame
                        row_frame = ctk.CTkFrame(rw_table_frame, fg_color="transparent")
                        row_frame.grid(row=row_idx, column=0, columnspan=3, sticky="ew", pady=0)
                        row_frame.grid_columnconfigure((0, 1, 2), weight=1)
                        
                        # Parameter name
                        name_label = ctk.CTkLabel(
                            row_frame,
                            text=param_display,
                            font=ctk.CTkFont(size=10),
                            height=18
                        )
                        name_label.grid(row=0, column=0, padx=8, pady=1)
                        
                        # Volatility
                        vol_label = ctk.CTkLabel(
                            row_frame,
                            text=f"{params.volatilities[param_key]:.6f}",
                            font=ctk.CTkFont(size=10),
                            height=18
                        )
                        vol_label.grid(row=0, column=1, padx=8, pady=1)
                        
                        # Reversion rate
                        rev_label = ctk.CTkLabel(
                            row_frame,
                            text=f"{params.reversion_rates[param_key]:.6f}",
                            font=ctk.CTkFont(size=10),
                            height=18
                        )
                        rev_label.grid(row=0, column=2, padx=8, pady=1)
                        
                        row_idx += 1
            
            logger.info("display_historical_parameters completed successfully")
            
        except Exception as e:
            logger.error(f"Error in display_historical_parameters: {e}", exc_info=True)
            # Show error to user
            error_label = ctk.CTkLabel(
                self.params_scrollable,
                text=f"Error displaying parameters: {str(e)}",
                font=ctk.CTkFont(size=12),
                text_color="red"
            )
            error_label.grid(row=0, column=0, padx=20, pady=20)
    
    def display_data_quality(self, params) -> None:
        """
        Display data quality metrics including gap analysis.
        
        Args:
            params: HistoricalParameters object with calculated values
        """
        # Check if we have precipitation data to analyze
        if self.app_state.precipitation_data is None or self.app_state.precipitation_data.empty:
            return
        
        # Data Quality Section Title
        quality_title = ctk.CTkLabel(
            self.params_scrollable,
            text="Data Quality",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        quality_title.grid(row=18, column=0, padx=10, pady=(15, 5), sticky="w")
        
        # Run gap analysis
        try:
            df = self.app_state.precipitation_data.copy()
            
            # Ensure DATE is index
            if 'DATE' in df.columns:
                df['DATE'] = pd.to_datetime(df['DATE'])
                df.set_index('DATE', inplace=True)
            elif not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # Analyze gaps
            gap_results = analyze_gaps(df, 'PRCP', gap_threshold=7)
            
            if gap_results:
                # Create summary frame
                summary_frame = ctk.CTkFrame(self.params_scrollable)
                summary_frame.grid(row=19, column=0, padx=10, pady=(5, 2), sticky="ew")
                summary_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
                
                # Summary metrics
                total_days = gap_results['total_days']
                missing_days = gap_results['total_missing_days']
                coverage_pct = round((total_days - missing_days) / total_days * 100, 1)
                
                metrics = [
                    ("Data Coverage", f"{coverage_pct}%"),
                    ("Missing Days", f"{missing_days} / {total_days}"),
                    ("Short Gaps (≤7d)", str(gap_results['short_gap_count'])),
                    ("Long Gaps (>7d)", str(gap_results['long_gap_count']))
                ]
                
                for col, (label, value) in enumerate(metrics):
                    metric_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
                    metric_frame.grid(row=0, column=col, padx=5, pady=5)
                    
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
                        font=ctk.CTkFont(size=12, weight="bold")
                    )
                    value_widget.pack()
                
                # Show long gaps if any exist
                if gap_results['long_gap_count'] > 0 and not gap_results['long_gaps'].empty:
                    long_gaps_title = ctk.CTkLabel(
                        self.params_scrollable,
                        text="Long Gaps (>7 days)",
                        font=ctk.CTkFont(size=12, weight="bold")
                    )
                    long_gaps_title.grid(row=20, column=0, padx=10, pady=(10, 2), sticky="w")
                    
                    # Create table for long gaps
                    gaps_frame = ctk.CTkFrame(self.params_scrollable)
                    gaps_frame.grid(row=21, column=0, padx=10, pady=(2, 5), sticky="ew")
                    gaps_frame.grid_columnconfigure((0, 1, 2), weight=1)
                    
                    # Headers
                    headers = ["Start Date", "End Date", "Duration (days)"]
                    for col, header in enumerate(headers):
                        label = ctk.CTkLabel(
                            gaps_frame,
                            text=header,
                            font=ctk.CTkFont(size=11, weight="bold")
                        )
                        label.grid(row=0, column=col, padx=5, pady=3)
                    
                    # Display up to 5 longest gaps
                    long_gaps_df = gap_results['long_gaps'].sort_values('duration', ascending=False).head(5)
                    
                    for idx, row in enumerate(long_gaps_df.itertuples(), start=1):
                        row_frame = ctk.CTkFrame(gaps_frame, fg_color="transparent")
                        row_frame.grid(row=idx, column=0, columnspan=3, sticky="ew", pady=1)
                        row_frame.grid_columnconfigure((0, 1, 2), weight=1)
                        
                        start_label = ctk.CTkLabel(
                            row_frame,
                            text=row.start_date.strftime('%Y-%m-%d'),
                            font=ctk.CTkFont(size=10)
                        )
                        start_label.grid(row=0, column=0, padx=5, pady=2)
                        
                        end_label = ctk.CTkLabel(
                            row_frame,
                            text=row.end_date.strftime('%Y-%m-%d'),
                            font=ctk.CTkFont(size=10)
                        )
                        end_label.grid(row=0, column=1, padx=5, pady=2)
                        
                        duration_label = ctk.CTkLabel(
                            row_frame,
                            text=str(row.duration),
                            font=ctk.CTkFont(size=10)
                        )
                        duration_label.grid(row=0, column=2, padx=5, pady=2)
                    
                    if len(gap_results['long_gaps']) > 5:
                        more_label = ctk.CTkLabel(
                            gaps_frame,
                            text=f"... and {len(gap_results['long_gaps']) - 5} more",
                            font=ctk.CTkFont(size=10),
                            text_color="gray"
                        )
                        more_label.grid(row=6, column=0, columnspan=3, pady=2)
        
        except Exception as e:
            logger.warning(f"Could not perform gap analysis: {e}")
            # Don't show error to user - gap analysis is optional
    
    def on_state_change(self, state_key: str, new_value) -> None:
        """
        React to application state changes.
        
        Args:
            state_key: Name of the state property that changed
            new_value: New value of the state property
        """
        logger.info(f"ParametersPanel.on_state_change called: {state_key} = {new_value}")
        
        # Update parameter display when historical parameters are calculated
        if state_key == 'historical_params' and new_value is not None:
            logger.info("Calling display_historical_parameters from on_state_change")
            self.display_historical_parameters(new_value)
            # Enable buttons when parameters are available
            self.export_button.configure(state="normal")
            self.plot_button.configure(state="normal")
    
    def on_export_clicked(self) -> None:
        """
        Handle export button click.
        
        Exports current parameters to the project folder via the
        CalibrationController.
        """
        # Check if parameters are available
        if not self.app_state.has_historical_params():
            messagebox.showerror(
                "Export Error",
                "No parameters available to export. Please calculate parameters first."
            )
            return
        
        # Disable export button and show progress
        self.export_button.configure(state="disabled")
        self.export_progress.grid()
        self.export_progress.configure(mode="indeterminate")
        self.export_progress.start()
        
        # Run export in background thread to prevent UI freezing
        def export_thread():
            result = self.calibration_controller.export_parameters()
            
            # Handle result on main thread
            self.after(0, lambda: self.handle_export_result(result))
        
        threading.Thread(target=export_thread, daemon=True).start()
    
    def handle_export_result(self, result) -> None:
        """
        Handle export result from CalibrationController.
        
        Args:
            result: Result object from export_parameters()
        """
        # Stop and hide progress indicator
        self.export_progress.stop()
        self.export_progress.grid_remove()
        
        # Re-enable export button
        self.export_button.configure(state="normal")
        
        if result.success:
            messagebox.showinfo(
                "Export Successful",
                f"Parameters exported to:\n{result.value}"
            )
        else:
            messagebox.showerror(
                "Export Failed",
                f"Failed to export parameters:\n{result.error}"
            )
    
    def on_plot_clicked(self) -> None:
        """
        Handle plot button click.
        
        Opens a new window with annual precipitation totals plot.
        """
        if not self.app_state.precipitation_data or self.app_state.precipitation_data.empty:
            messagebox.showerror(
                "No Data",
                "No precipitation data available to plot."
            )
            return
        
        # Create plot window
        self.create_plot_window()
    
    def create_plot_window(self) -> None:
        """
        Create a new window with precipitation data plot.
        """
        # Create new top-level window
        plot_window = ctk.CTkToplevel(self)
        plot_window.title("Precipitation Data - Annual Totals")
        plot_window.geometry("900x600")
        
        # Configure grid
        plot_window.grid_rowconfigure(0, weight=1)
        plot_window.grid_columnconfigure(0, weight=1)
        
        try:
            # Prepare data
            df = self.app_state.precipitation_data.copy()
            
            # Ensure DATE is index
            if 'DATE' in df.columns:
                df['DATE'] = pd.to_datetime(df['DATE'])
                df.set_index('DATE', inplace=True)
            elif not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # Calculate annual totals
            annual_totals = df['PRCP'].resample('YE').sum()
            
            # Create figure
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            # Plot annual totals
            years = annual_totals.index.year
            totals = annual_totals.values
            
            ax.plot(years, totals, marker='o', linewidth=2, markersize=6, color='#1f77b4')
            ax.fill_between(years, totals, alpha=0.3, color='#1f77b4')
            
            # Add mean line
            mean_total = totals.mean()
            ax.axhline(y=mean_total, color='red', linestyle='--', linewidth=1.5, 
                      label=f'Mean: {mean_total:.1f} mm/year')
            
            # Formatting
            ax.set_xlabel('Year', fontsize=12)
            ax.set_ylabel('Annual Precipitation (mm)', fontsize=12)
            ax.set_title('Annual Precipitation Totals', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='best')
            
            # Add statistics text box
            stats_text = (
                f"Mean: {mean_total:.1f} mm/year\n"
                f"Min: {totals.min():.1f} mm ({years[totals.argmin()]})\n"
                f"Max: {totals.max():.1f} mm ({years[totals.argmax()]})\n"
                f"Std Dev: {totals.std():.1f} mm"
            )
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                   fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
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
            logger.error(f"Error creating plot: {e}", exc_info=True)
            plot_window.destroy()
            messagebox.showerror(
                "Plot Error",
                f"Could not create plot:\n{e}"
            )
    
    def destroy(self) -> None:
        """
        Clean up resources when panel is destroyed.
        
        Unregisters the state observer before destroying the widget.
        """
        # Unregister observer
        self.app_state.unregister_observer(self.on_state_change)
        
        # Call parent destroy
        super().destroy()
