"""
Calibration panel view component for PrecipGen Desktop.

This module provides the UI for interactive parameter calibration with
sliders for adjusting α, β, and transition probabilities, along with
real-time deviation display and visualization.
"""

import logging
import customtkinter as ctk
from typing import Dict, Optional
from tkinter import messagebox
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

from precipgen.desktop.controllers.calibration_controller import CalibrationController
from precipgen.desktop.models.app_state import AppState


# Configure logging
logger = logging.getLogger(__name__)


class CalibrationPanel(ctk.CTkFrame):
    """
    UI component for parameter adjustment and visualization.
    
    Provides interactive sliders for adjusting precipitation model parameters
    (α, β, and transition probabilities) with real-time feedback showing
    current values and deviations from historical baseline. Includes reset
    and export functionality.
    
    Attributes:
        calibration_controller: Controller for parameter operations
        app_state: Application state manager
        alpha_sliders: Dictionary of sliders for alpha parameters (by month)
        beta_sliders: Dictionary of sliders for beta parameters (by month)
        transition_sliders: Dictionary of sliders for transition probabilities
        value_labels: Dictionary of labels displaying current parameter values
        deviation_labels: Dictionary of labels displaying deviations
    """
    
    def __init__(
        self,
        parent,
        calibration_controller: CalibrationController,
        app_state: AppState
    ):
        """
        Initialize CalibrationPanel.
        
        Args:
            parent: Parent widget (typically MainWindow content area)
            calibration_controller: CalibrationController instance
            app_state: AppState instance for observing state changes
        """
        super().__init__(parent, corner_radius=0)
        
        self.calibration_controller = calibration_controller
        self.app_state = app_state
        
        # Store slider and label references
        self.alpha_sliders: Dict[int, ctk.CTkSlider] = {}
        self.beta_sliders: Dict[int, ctk.CTkSlider] = {}
        self.transition_sliders: Dict[str, Dict[int, ctk.CTkSlider]] = {}
        self.value_labels: Dict[str, Dict[int, ctk.CTkLabel]] = {}
        self.deviation_labels: Dict[str, Dict[int, ctk.CTkLabel]] = {}
        
        # Current selected month for parameter adjustment
        self.selected_month: int = 1
        
        # Matplotlib figure and canvas for visualization
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None
        
        # Setup the panel layout
        self.setup_ui()
        
        # Register as observer for state changes
        self.app_state.register_observer(self.on_state_change)
    
    def setup_ui(self) -> None:
        """
        Configure the panel layout and widgets.
        
        Creates a layout with title, month selector, parameter sliders,
        control buttons (reset, export), and visualization area.
        """
        # Configure grid layout - split into left (controls) and right (visualization)
        self.grid_rowconfigure(0, weight=0)  # Title
        self.grid_rowconfigure(1, weight=0)  # Month selector
        self.grid_rowconfigure(2, weight=1)  # Main content (parameters + visualization)
        self.grid_rowconfigure(3, weight=0)  # Control buttons
        self.grid_columnconfigure(0, weight=1)
        
        # Title label
        title_label = ctk.CTkLabel(
            self,
            text="Parameter Calibration",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Month selector frame
        self.month_frame = self.create_month_selector()
        self.month_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # Main content frame - split into parameters (left) and visualization (right)
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)  # Parameters
        content_frame.grid_columnconfigure(1, weight=2)  # Visualization (larger)
        
        # Parameters frame (sliders and values) - left side
        self.params_frame = self.create_parameters_frame()
        self.params_frame.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        
        # Visualization frame - right side
        self.viz_frame = self.create_visualization_frame()
        self.viz_frame.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")
        
        # Control buttons frame (reset, export)
        self.controls_frame = self.create_controls_frame()
        self.controls_frame.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        # Initially disable controls until parameters are available
        self.update_controls_state()
    
    def create_month_selector(self) -> ctk.CTkFrame:
        """
        Create month selection interface.
        
        Returns:
            Frame containing month selection dropdown
        """
        frame = ctk.CTkFrame(self)
        frame.grid_columnconfigure(1, weight=1)
        
        # Month label
        ctk.CTkLabel(
            frame,
            text="Month:",
            font=ctk.CTkFont(size=14)
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Month dropdown
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        self.month_selector = ctk.CTkOptionMenu(
            frame,
            values=month_names,
            command=self.on_month_changed
        )
        self.month_selector.set("January")
        self.month_selector.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        return frame
    
    def create_parameters_frame(self) -> ctk.CTkFrame:
        """
        Create parameter sliders and value displays.
        
        Returns:
            Frame containing all parameter sliders with labels
        """
        frame = ctk.CTkFrame(self)
        frame.grid_columnconfigure(0, weight=1)
        
        # Create scrollable frame for parameters
        scrollable = ctk.CTkScrollableFrame(frame, label_text="Parameters")
        scrollable.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        scrollable.grid_columnconfigure(1, weight=1)
        
        frame.grid_rowconfigure(0, weight=1)
        
        row = 0
        
        # Alpha parameter
        row = self.create_parameter_slider(
            scrollable,
            row,
            "Alpha (α)",
            "alpha",
            min_value=0.1,
            max_value=5.0,
            step=0.01
        )
        
        # Beta parameter
        row = self.create_parameter_slider(
            scrollable,
            row,
            "Beta (β)",
            "beta",
            min_value=0.1,
            max_value=5.0,
            step=0.01
        )
        
        # Transition probabilities
        row = self.create_parameter_slider(
            scrollable,
            row,
            "P(W|W) - Wet given Wet",
            "p_wet_wet",
            min_value=0.0,
            max_value=1.0,
            step=0.01
        )
        
        row = self.create_parameter_slider(
            scrollable,
            row,
            "P(W|D) - Wet given Dry",
            "p_wet_dry",
            min_value=0.0,
            max_value=1.0,
            step=0.01
        )
        
        row = self.create_parameter_slider(
            scrollable,
            row,
            "P(D|W) - Dry given Wet",
            "p_dry_wet",
            min_value=0.0,
            max_value=1.0,
            step=0.01
        )
        
        row = self.create_parameter_slider(
            scrollable,
            row,
            "P(D|D) - Dry given Dry",
            "p_dry_dry",
            min_value=0.0,
            max_value=1.0,
            step=0.01
        )
        
        return frame
    
    def create_parameter_slider(
        self,
        parent,
        row: int,
        label_text: str,
        param_name: str,
        min_value: float,
        max_value: float,
        step: float
    ) -> int:
        """
        Create a parameter slider with label, value display, and deviation.
        
        Args:
            parent: Parent widget for the slider
            row: Starting row for grid placement
            label_text: Display label for the parameter
            param_name: Internal parameter name (e.g., 'alpha', 'p_wet_wet')
            min_value: Minimum slider value
            max_value: Maximum slider value
            step: Slider step size
            
        Returns:
            Next available row number
        """
        # Parameter label
        label = ctk.CTkLabel(
            parent,
            text=label_text,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        label.grid(row=row, column=0, padx=10, pady=(15, 5), sticky="w")
        
        row += 1
        
        # Slider
        slider = ctk.CTkSlider(
            parent,
            from_=min_value,
            to=max_value,
            number_of_steps=int((max_value - min_value) / step),
            command=lambda value, pn=param_name: self.on_slider_changed(pn, value)
        )
        slider.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        slider.set((min_value + max_value) / 2)  # Default to middle
        
        # Store slider reference
        if param_name not in self.value_labels:
            self.value_labels[param_name] = {}
            self.deviation_labels[param_name] = {}
        
        # Store slider based on parameter type
        if param_name == "alpha":
            self.alpha_sliders[self.selected_month] = slider
        elif param_name == "beta":
            self.beta_sliders[self.selected_month] = slider
        else:
            if param_name not in self.transition_sliders:
                self.transition_sliders[param_name] = {}
            self.transition_sliders[param_name][self.selected_month] = slider
        
        row += 1
        
        # Value and deviation display frame
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="ew")
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=1)
        
        # Current value label
        value_label = ctk.CTkLabel(
            info_frame,
            text=f"Value: {(min_value + max_value) / 2:.3f}",
            font=ctk.CTkFont(size=12)
        )
        value_label.grid(row=0, column=0, padx=5, sticky="w")
        self.value_labels[param_name][self.selected_month] = value_label
        
        # Deviation label
        deviation_label = ctk.CTkLabel(
            info_frame,
            text="Deviation: 0.000",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        deviation_label.grid(row=0, column=1, padx=5, sticky="e")
        self.deviation_labels[param_name][self.selected_month] = deviation_label
        
        row += 1
        
        return row
    
    def create_visualization_frame(self) -> ctk.CTkFrame:
        """
        Create visualization area with matplotlib canvas.
        
        Displays statistical summaries and charts showing parameter impact.
        Updates in real-time as parameters are adjusted.
        
        Requirements: 6.2, 6.4, 6.5
        
        Returns:
            Frame containing matplotlib canvas for visualizations
        """
        frame = ctk.CTkFrame(self)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Create matplotlib figure with subplots
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.figure.patch.set_facecolor('#2b2b2b')  # Match CustomTkinter dark theme
        
        # Create canvas to embed matplotlib figure
        self.canvas = FigureCanvasTkAgg(self.figure, master=frame)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Initial empty visualization
        self.update_visualization()
        
        return frame
    
    def update_visualization(self) -> None:
        """
        Refresh charts based on current parameters.
        
        Displays statistical summaries calculated using current parameter values
        (historical or adjusted). Updates within 100ms for real-time feedback.
        
        Requirements: 6.1, 6.2, 6.4, 6.5
        """
        if not self.figure or not self.canvas:
            return
        
        # Clear previous plots
        self.figure.clear()
        
        # Check if parameters are available
        if not self.app_state.has_historical_params():
            # Show placeholder message
            ax = self.figure.add_subplot(111)
            ax.text(
                0.5, 0.5,
                'No parameters available.\nPlease calculate parameters first.',
                horizontalalignment='center',
                verticalalignment='center',
                transform=ax.transAxes,
                fontsize=14,
                color='white'
            )
            ax.set_facecolor('#2b2b2b')
            ax.axis('off')
            self.canvas.draw()
            return
        
        # Get current parameters (adjusted if available, otherwise historical)
        if self.app_state.has_adjusted_params():
            current_params = self.app_state.adjusted_params
            title_suffix = " (Adjusted)"
        else:
            current_params = self.app_state.historical_params
            title_suffix = " (Historical)"
        
        historical_params = self.app_state.historical_params
        
        # Create 2x2 subplot layout
        # Top left: Alpha and Beta by month
        ax1 = self.figure.add_subplot(2, 2, 1)
        self._plot_alpha_beta(ax1, current_params, historical_params, title_suffix)
        
        # Top right: Transition probabilities by month
        ax2 = self.figure.add_subplot(2, 2, 2)
        self._plot_transition_probs(ax2, current_params, historical_params, title_suffix)
        
        # Bottom left: Statistical summary for selected month
        ax3 = self.figure.add_subplot(2, 2, 3)
        self._plot_monthly_summary(ax3, current_params, historical_params)
        
        # Bottom right: Parameter deviations
        ax4 = self.figure.add_subplot(2, 2, 4)
        self._plot_deviations(ax4, current_params, historical_params)
        
        # Adjust layout to prevent overlap
        self.figure.tight_layout(pad=2.0)
        
        # Redraw canvas (Requirement 6.1: within 100ms)
        self.canvas.draw()
    
    def _plot_alpha_beta(self, ax, current_params, historical_params, title_suffix: str) -> None:
        """
        Plot alpha and beta parameters by month.
        
        Args:
            ax: Matplotlib axes object
            current_params: Current parameter values
            historical_params: Historical parameter values
            title_suffix: Suffix for plot title (e.g., " (Adjusted)")
        """
        months = range(1, 13)
        
        # Extract alpha and beta values for all months
        alpha_current = [float(current_params.alpha.iloc[i, 0]) for i in range(12)]
        beta_current = [float(current_params.beta.iloc[i, 0]) for i in range(12)]
        
        alpha_historical = [float(historical_params.alpha.iloc[i, 0]) for i in range(12)]
        beta_historical = [float(historical_params.beta.iloc[i, 0]) for i in range(12)]
        
        # Plot lines
        ax.plot(months, alpha_current, 'o-', label='α (current)', color='#1f77b4', linewidth=2)
        ax.plot(months, beta_current, 's-', label='β (current)', color='#ff7f0e', linewidth=2)
        
        # Plot historical as dashed lines if different
        if self.app_state.has_adjusted_params():
            ax.plot(months, alpha_historical, '--', label='α (historical)', color='#1f77b4', alpha=0.5)
            ax.plot(months, beta_historical, '--', label='β (historical)', color='#ff7f0e', alpha=0.5)
        
        # Highlight selected month
        month_idx = self.selected_month - 1
        ax.axvline(x=self.selected_month, color='yellow', linestyle=':', alpha=0.5, linewidth=1)
        
        ax.set_xlabel('Month', color='white')
        ax.set_ylabel('Parameter Value', color='white')
        ax.set_title(f'α and β Parameters{title_suffix}', color='white', fontsize=10)
        ax.legend(fontsize=8, loc='best')
        ax.grid(True, alpha=0.3)
        ax.set_facecolor('#2b2b2b')
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['top'].set_color('#2b2b2b')
        ax.spines['right'].set_color('#2b2b2b')
    
    def _plot_transition_probs(self, ax, current_params, historical_params, title_suffix: str) -> None:
        """
        Plot transition probabilities by month.
        
        Args:
            ax: Matplotlib axes object
            current_params: Current parameter values
            historical_params: Historical parameter values
            title_suffix: Suffix for plot title
        """
        months = range(1, 13)
        
        # Extract transition probability values
        pww_current = [float(current_params.p_wet_wet.iloc[i, 0]) for i in range(12)]
        pwd_current = [float(current_params.p_wet_dry.iloc[i, 0]) for i in range(12)]
        
        # Plot lines
        ax.plot(months, pww_current, 'o-', label='P(W|W)', color='#2ca02c', linewidth=2)
        ax.plot(months, pwd_current, 's-', label='P(W|D)', color='#d62728', linewidth=2)
        
        # Plot historical if different
        if self.app_state.has_adjusted_params():
            pww_historical = [float(historical_params.p_wet_wet.iloc[i, 0]) for i in range(12)]
            pwd_historical = [float(historical_params.p_wet_dry.iloc[i, 0]) for i in range(12)]
            ax.plot(months, pww_historical, '--', label='P(W|W) hist', color='#2ca02c', alpha=0.5)
            ax.plot(months, pwd_historical, '--', label='P(W|D) hist', color='#d62728', alpha=0.5)
        
        # Highlight selected month
        ax.axvline(x=self.selected_month, color='yellow', linestyle=':', alpha=0.5, linewidth=1)
        
        ax.set_xlabel('Month', color='white')
        ax.set_ylabel('Probability', color='white')
        ax.set_title(f'Transition Probabilities{title_suffix}', color='white', fontsize=10)
        ax.set_ylim([0, 1])
        ax.legend(fontsize=8, loc='best')
        ax.grid(True, alpha=0.3)
        ax.set_facecolor('#2b2b2b')
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['top'].set_color('#2b2b2b')
        ax.spines['right'].set_color('#2b2b2b')
    
    def _plot_monthly_summary(self, ax, current_params, historical_params) -> None:
        """
        Plot statistical summary for selected month.
        
        Shows current parameter values for the selected month in a table format.
        
        Requirement 6.2: Statistical summaries reflect current parameter values
        
        Args:
            ax: Matplotlib axes object
            current_params: Current parameter values
            historical_params: Historical parameter values
        """
        month_idx = self.selected_month - 1
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Extract values for selected month
        alpha = float(current_params.alpha.iloc[month_idx, 0])
        beta = float(current_params.beta.iloc[month_idx, 0])
        pww = float(current_params.p_wet_wet.iloc[month_idx, 0])
        pwd = float(current_params.p_wet_dry.iloc[month_idx, 0])
        pdw = float(current_params.p_dry_wet.iloc[month_idx, 0])
        pdd = float(current_params.p_dry_dry.iloc[month_idx, 0])
        
        # Create table data
        params = ['α', 'β', 'P(W|W)', 'P(W|D)', 'P(D|W)', 'P(D|D)']
        values = [alpha, beta, pww, pwd, pdw, pdd]
        
        # Calculate deviations if adjusted
        if self.app_state.has_adjusted_params():
            alpha_hist = float(historical_params.alpha.iloc[month_idx, 0])
            beta_hist = float(historical_params.beta.iloc[month_idx, 0])
            pww_hist = float(historical_params.p_wet_wet.iloc[month_idx, 0])
            pwd_hist = float(historical_params.p_wet_dry.iloc[month_idx, 0])
            pdw_hist = float(historical_params.p_dry_wet.iloc[month_idx, 0])
            pdd_hist = float(historical_params.p_dry_dry.iloc[month_idx, 0])
            
            hist_values = [alpha_hist, beta_hist, pww_hist, pwd_hist, pdw_hist, pdd_hist]
            deviations = [f'{v - h:+.3f}' for v, h in zip(values, hist_values)]
        else:
            deviations = ['0.000'] * 6
        
        # Format values
        value_strs = [f'{v:.3f}' for v in values]
        
        # Create table
        table_data = []
        for param, value, dev in zip(params, value_strs, deviations):
            table_data.append([param, value, dev])
        
        # Clear axes and create table
        ax.axis('off')
        ax.set_facecolor('#2b2b2b')
        
        table = ax.table(
            cellText=table_data,
            colLabels=['Parameter', 'Value', 'Δ from Hist'],
            cellLoc='center',
            loc='center',
            colWidths=[0.3, 0.35, 0.35]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Style table
        for (i, j), cell in table.get_celld().items():
            if i == 0:  # Header row
                cell.set_facecolor('#1f77b4')
                cell.set_text_props(weight='bold', color='white')
            else:
                cell.set_facecolor('#3b3b3b')
                cell.set_text_props(color='white')
                
                # Highlight deviations
                if j == 2 and table_data[i-1][2] != '0.000':
                    cell.set_facecolor('#ff7f0e')
        
        ax.set_title(f'Parameters for {month_names[month_idx]}', color='white', fontsize=10, pad=10)
    
    def _plot_deviations(self, ax, current_params, historical_params) -> None:
        """
        Plot parameter deviations from historical values.
        
        Shows bar chart of deviations for the selected month.
        
        Requirement 6.3: Highlight which values differ from historical
        
        Args:
            ax: Matplotlib axes object
            current_params: Current parameter values
            historical_params: Historical parameter values
        """
        if not self.app_state.has_adjusted_params():
            # No deviations if using historical parameters
            ax.text(
                0.5, 0.5,
                'No adjustments made.\nAll parameters at historical values.',
                horizontalalignment='center',
                verticalalignment='center',
                transform=ax.transAxes,
                fontsize=10,
                color='white'
            )
            ax.set_facecolor('#2b2b2b')
            ax.axis('off')
            return
        
        month_idx = self.selected_month - 1
        
        # Calculate deviations for selected month
        alpha_dev = float(current_params.alpha.iloc[month_idx, 0]) - float(historical_params.alpha.iloc[month_idx, 0])
        beta_dev = float(current_params.beta.iloc[month_idx, 0]) - float(historical_params.beta.iloc[month_idx, 0])
        pww_dev = float(current_params.p_wet_wet.iloc[month_idx, 0]) - float(historical_params.p_wet_wet.iloc[month_idx, 0])
        pwd_dev = float(current_params.p_wet_dry.iloc[month_idx, 0]) - float(historical_params.p_wet_dry.iloc[month_idx, 0])
        
        params = ['α', 'β', 'P(W|W)', 'P(W|D)']
        deviations = [alpha_dev, beta_dev, pww_dev, pwd_dev]
        
        # Color bars based on deviation direction
        colors = ['#2ca02c' if d >= 0 else '#d62728' for d in deviations]
        
        # Create bar chart
        bars = ax.barh(params, deviations, color=colors, alpha=0.7)
        
        # Add value labels on bars
        for bar, dev in zip(bars, deviations):
            width = bar.get_width()
            label_x = width + (0.01 if width >= 0 else -0.01)
            ax.text(
                label_x, bar.get_y() + bar.get_height()/2,
                f'{dev:+.3f}',
                ha='left' if width >= 0 else 'right',
                va='center',
                color='white',
                fontsize=9
            )
        
        ax.axvline(x=0, color='white', linestyle='-', linewidth=0.8)
        ax.set_xlabel('Deviation from Historical', color='white')
        ax.set_title('Parameter Deviations', color='white', fontsize=10)
        ax.set_facecolor('#2b2b2b')
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['top'].set_color('#2b2b2b')
        ax.spines['right'].set_color('#2b2b2b')
        ax.grid(True, axis='x', alpha=0.3)
    
    def create_controls_frame(self) -> ctk.CTkFrame:
        """
        Create control buttons (reset, export).
        
        Returns:
            Frame containing control buttons
        """
        frame = ctk.CTkFrame(self)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        
        # Reset button
        self.reset_button = ctk.CTkButton(
            frame,
            text="Reset to Historical",
            command=self.on_reset_clicked
        )
        self.reset_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Export button
        self.export_button = ctk.CTkButton(
            frame,
            text="Export Parameters",
            command=self.on_export_clicked
        )
        self.export_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Export progress indicator (Requirement 11.5)
        self.export_progress = ctk.CTkProgressBar(frame)
        self.export_progress.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        self.export_progress.set(0)
        self.export_progress.grid_remove()  # Hide initially
        
        return frame
    
    def on_month_changed(self, month_name: str) -> None:
        """
        Handle month selection change.
        
        Args:
            month_name: Selected month name (e.g., "January")
        """
        # Convert month name to number (1-12)
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        self.selected_month = month_names.index(month_name) + 1
        
        # Update sliders and displays for the new month
        self.update_parameter_displays()
        
        # Update visualization to show new month (Requirement 6.4)
        self.update_visualization()
    
    def on_slider_changed(self, param_name: str, value: float) -> None:
        """
        Handle slider movement with immediate feedback.
        
        Connects slider events to CalibrationController to update parameter
        values immediately on slider change. Updates value display and
        highlights deviations from historical values.
        
        Requirements: 5.2, 5.3, 6.1, 6.3
        
        Args:
            param_name: Name of parameter being adjusted
            value: New parameter value from slider
        """
        # Update value label immediately for visual feedback (Requirement 6.1)
        if param_name in self.value_labels and self.selected_month in self.value_labels[param_name]:
            self.value_labels[param_name][self.selected_month].configure(
                text=f"Value: {value:.3f}"
            )
        
        # Update parameter via controller (Requirement 5.2)
        result = self.calibration_controller.adjust_parameter(
            param_name,
            self.selected_month,
            value
        )
        
        if not result.success:
            # Show error if adjustment failed
            messagebox.showerror(
                "Parameter Adjustment Error",
                result.error
            )
            # Revert slider to previous value
            self.update_parameter_displays()
            return
        
        # Calculate and display deviation (Requirements 5.3, 6.3)
        if self.app_state.has_historical_params():
            historical = self.app_state.historical_params
            
            # Get historical value for this parameter and month
            month_idx = self.selected_month - 1
            
            try:
                historical_value = self._get_historical_value(param_name, month_idx)
                deviation = value - historical_value
                
                # Update deviation label with color coding (Requirement 6.3)
                if param_name in self.deviation_labels and self.selected_month in self.deviation_labels[param_name]:
                    deviation_text = f"Deviation: {deviation:+.3f}"
                    
                    # Color code: green for historical (zero deviation), orange for adjusted
                    if abs(deviation) < 0.001:
                        color = "green"
                    else:
                        color = "orange"
                    
                    self.deviation_labels[param_name][self.selected_month].configure(
                        text=deviation_text,
                        text_color=color
                    )
            
            except (IndexError, ValueError, TypeError):
                # Handle missing or invalid data gracefully
                pass
        
        # Update visualization in real-time (Requirement 6.1, 6.4)
        self.update_visualization()
    
    def on_reset_clicked(self) -> None:
        """
        Handle reset button click.
        
        Resets all parameters to historical values via the CalibrationController
        and updates all UI elements to reflect the reset state.
        
        Requirements: 5.4, 6.5
        """
        # Check if parameters are available
        if not self.app_state.has_historical_params():
            messagebox.showerror(
                "Reset Error",
                "No historical parameters available. Please calculate parameters first."
            )
            return
        
        # Reset parameters via controller (Requirement 5.4)
        result = self.calibration_controller.reset_to_historical()
        
        if result.success:
            # Update all displays (Requirement 6.5)
            self.update_parameter_displays()
            
            # Update visualization (Requirement 6.5)
            self.update_visualization()
            
            messagebox.showinfo(
                "Reset Successful",
                "All parameters have been reset to historical values."
            )
        else:
            messagebox.showerror(
                "Reset Failed",
                f"Failed to reset parameters:\n{result.error}"
            )
    
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
        
        # Disable export button and show progress (Requirement 11.5)
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
    
    def on_state_change(self, state_key: str, new_value) -> None:
        """
        React to application state changes.
        
        Updates UI elements when relevant state properties change,
        particularly when historical or adjusted parameters are updated.
        
        Args:
            state_key: Name of the state property that changed
            new_value: New value of the state property
        """
        if state_key in ['historical_params', 'adjusted_params']:
            self.update_parameter_displays()
            self.update_controls_state()
            # Update visualization when parameters change (Requirement 6.4)
            self.update_visualization()
    
    def update_parameter_displays(self) -> None:
        """
        Update all parameter sliders and labels with current values.
        
        Reads current parameter values from app state (adjusted or historical)
        and updates slider positions, value labels, and deviation displays.
        """
        # Check if parameters are available
        if not self.app_state.has_historical_params():
            return
        
        # Get current parameters (adjusted if available, otherwise historical)
        if self.app_state.has_adjusted_params():
            params = self.app_state.adjusted_params
        else:
            params = self.app_state.historical_params
        
        # Get historical parameters for deviation calculation
        historical = self.app_state.historical_params
        
        # Update each parameter
        self._update_parameter_display('alpha', params.alpha, historical.alpha)
        self._update_parameter_display('beta', params.beta, historical.beta)
        self._update_parameter_display('p_wet_wet', params.p_wet_wet, historical.p_wet_wet)
        self._update_parameter_display('p_wet_dry', params.p_wet_dry, historical.p_wet_dry)
        self._update_parameter_display('p_dry_wet', params.p_dry_wet, historical.p_dry_wet)
        self._update_parameter_display('p_dry_dry', params.p_dry_dry, historical.p_dry_dry)
    
    def _update_parameter_display(
        self,
        param_name: str,
        current_values,
        historical_values
    ) -> None:
        """
        Update a single parameter's slider and labels.
        
        Args:
            param_name: Parameter name (e.g., 'alpha', 'p_wet_wet')
            current_values: Current parameter values (DataFrame)
            historical_values: Historical parameter values (DataFrame)
        """
        # Get value for selected month (month is 1-indexed, DataFrame is 0-indexed)
        month_idx = self.selected_month - 1
        
        try:
            current_value = float(current_values.iloc[month_idx, 0])
            historical_value = float(historical_values.iloc[month_idx, 0])
            deviation = current_value - historical_value
            
            # Update slider
            slider = self._get_slider(param_name)
            if slider:
                slider.set(current_value)
            
            # Update value label
            if param_name in self.value_labels and self.selected_month in self.value_labels[param_name]:
                self.value_labels[param_name][self.selected_month].configure(
                    text=f"Value: {current_value:.3f}"
                )
            
            # Update deviation label with color coding
            if param_name in self.deviation_labels and self.selected_month in self.deviation_labels[param_name]:
                deviation_text = f"Deviation: {deviation:+.3f}"
                
                # Color code: green for historical (zero deviation), yellow for adjusted
                if abs(deviation) < 0.001:
                    color = "green"
                else:
                    color = "orange"
                
                self.deviation_labels[param_name][self.selected_month].configure(
                    text=deviation_text,
                    text_color=color
                )
        
        except (IndexError, ValueError, TypeError) as e:
            # Handle missing or invalid data gracefully
            pass
    
    def _get_slider(self, param_name: str) -> Optional[ctk.CTkSlider]:
        """
        Get slider widget for a parameter.
        
        Args:
            param_name: Parameter name
            
        Returns:
            Slider widget or None if not found
        """
        if param_name == "alpha" and self.selected_month in self.alpha_sliders:
            return self.alpha_sliders[self.selected_month]
        elif param_name == "beta" and self.selected_month in self.beta_sliders:
            return self.beta_sliders[self.selected_month]
        elif param_name in self.transition_sliders and self.selected_month in self.transition_sliders[param_name]:
            return self.transition_sliders[param_name][self.selected_month]
        
        return None
    
    def _get_historical_value(self, param_name: str, month_idx: int) -> float:
        """
        Get historical value for a parameter and month.
        
        Args:
            param_name: Parameter name (e.g., 'alpha', 'p_wet_wet')
            month_idx: Month index (0-11)
            
        Returns:
            Historical parameter value
        """
        historical = self.app_state.historical_params
        
        if param_name == 'alpha':
            return float(historical.alpha.iloc[month_idx, 0])
        elif param_name == 'beta':
            return float(historical.beta.iloc[month_idx, 0])
        elif param_name == 'p_wet_wet':
            return float(historical.p_wet_wet.iloc[month_idx, 0])
        elif param_name == 'p_wet_dry':
            return float(historical.p_wet_dry.iloc[month_idx, 0])
        elif param_name == 'p_dry_wet':
            return float(historical.p_dry_wet.iloc[month_idx, 0])
        elif param_name == 'p_dry_dry':
            return float(historical.p_dry_dry.iloc[month_idx, 0])
        else:
            raise ValueError(f"Unknown parameter: {param_name}")
    
    def update_controls_state(self) -> None:
        """
        Enable or disable control buttons based on state.
        
        Enables buttons only when parameters are available.
        """
        has_params = self.app_state.has_historical_params()
        
        # Enable/disable buttons
        state = "normal" if has_params else "disabled"
        self.reset_button.configure(state=state)
        self.export_button.configure(state=state)
        
        # Also disable month selector if no parameters
        self.month_selector.configure(state=state)
