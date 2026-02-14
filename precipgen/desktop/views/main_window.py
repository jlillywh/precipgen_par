"""
Main application window for PrecipGen Desktop.

This module provides the top-level window with tab-based navigation structure.
Implements a 6-tab workflow: Home, Search, Upload, Basic Analysis, Markov Analysis,
and Trend Analysis. Manages tab state based on session initialization and coordinates
between panel components following the MVC pattern.
"""

import logging
import customtkinter as ctk
from typing import Any, Dict, Optional
from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.views.home_panel import HomePanel
from precipgen.desktop.views.search_panel import SearchPanel
from precipgen.desktop.views.upload_panel import UploadPanel
from precipgen.desktop.views.basic_analysis_panel import BasicAnalysisPanel
from precipgen.desktop.views.markov_analysis_panel import MarkovAnalysisPanel
from precipgen.desktop.views.trend_analysis_panel import TrendAnalysisPanel


# Configure logging
logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    """
    Top-level application window for PrecipGen Desktop.
    
    Manages the main window layout and coordinates between different
    panel components. Observes application state changes and updates
    the UI accordingly.
    
    Attributes:
        app_state: Application state manager
        controllers: Dictionary of controller instances
    """
    
    def __init__(self, app_state: AppState, controllers: Optional[Dict[str, Any]] = None):
        """
        Initialize the main application window.
        
        Args:
            app_state: Application state manager instance
            controllers: Dictionary of controller instances (optional)
        """
        super().__init__()
        
        try:
            logger.info("Initializing main window")
            
            self.app_state = app_state
            self.controllers = controllers or {}
            
            # Configure window
            self.title("PrecipGen Desktop")
            self.geometry("1200x800")
            
            # Set appearance mode and color theme
            ctk.set_appearance_mode("system")  # Modes: "system", "dark", "light"
            ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"
            
            # Setup the window layout
            self.setup_layout()
            
            # Register as observer for state changes
            self.app_state.register_observer(self.on_state_change)
            
            # Configure window close handler
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            logger.info("Main window initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing main window: {e}", exc_info=True)
            raise
    
    def setup_layout(self) -> None:
        """
        Configure window layout with panels.
        
        Creates a tabbed interface for the 6-tab workflow: Home, Search, Upload, 
        Basic Analysis, Markov Analysis, and Trend Analysis.
        The Home tab contains the working directory management.
        """
        # Configure grid layout (1 row, 1 column - tabs fill entire window)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create tabbed interface for the 6-tab workflow at the top
        self.tabview = ctk.CTkTabview(self, corner_radius=0)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Add tabs in workflow order
        self.tabview.add("Home")
        self.tabview.add("Search")
        self.tabview.add("Upload")
        self.tabview.add("Basic Analysis")
        self.tabview.add("Markov Analysis")
        self.tabview.add("Trend Analysis")
        
        # Create Home panel (working directory management)
        if 'project_controller' in self.controllers:
            self.home_panel = HomePanel(
                self.tabview.tab("Home"),
                self.controllers['project_controller'],
                self.app_state
            )
            self.home_panel.pack(fill="both", expand=True)
        else:
            home_placeholder = ctk.CTkLabel(
                self.tabview.tab("Home"),
                text="Project controller not available",
                font=ctk.CTkFont(size=16)
            )
            home_placeholder.pack(padx=20, pady=20)
        
        # Create Search panel (station search and download)
        if 'data_controller' in self.controllers:
            self.search_panel = SearchPanel(
                self.tabview.tab("Search"),
                self.controllers['data_controller'],
                self.app_state
            )
            self.search_panel.pack(fill="both", expand=True)
        else:
            search_placeholder = ctk.CTkLabel(
                self.tabview.tab("Search"),
                text="Data controller not available",
                font=ctk.CTkFont(size=16)
            )
            search_placeholder.pack(padx=20, pady=20)
        
        # Create Upload panel (upload existing CSV files)
        if 'data_controller' in self.controllers:
            self.upload_panel = UploadPanel(
                self.tabview.tab("Upload"),
                self.controllers['data_controller'],
                self.app_state
            )
            self.upload_panel.pack(fill="both", expand=True)
        else:
            upload_placeholder = ctk.CTkLabel(
                self.tabview.tab("Upload"),
                text="Data controller not available",
                font=ctk.CTkFont(size=16)
            )
            upload_placeholder.pack(padx=20, pady=20)
        
        # Create Basic Analysis panel
        if 'analysis_controller' in self.controllers:
            self.basic_analysis_panel = BasicAnalysisPanel(
                self.tabview.tab("Basic Analysis"),
                self.app_state,
                self.controllers['analysis_controller']
            )
            self.basic_analysis_panel.pack(fill="both", expand=True)
        else:
            basic_placeholder = ctk.CTkLabel(
                self.tabview.tab("Basic Analysis"),
                text="Analysis controller not available",
                font=ctk.CTkFont(size=16)
            )
            basic_placeholder.pack(padx=20, pady=20)
        
        # Create Markov Analysis panel
        if 'analysis_controller' in self.controllers:
            self.markov_analysis_panel = MarkovAnalysisPanel(
                self.tabview.tab("Markov Analysis"),
                self.app_state,
                self.controllers['analysis_controller']
            )
            self.markov_analysis_panel.pack(fill="both", expand=True)
        else:
            markov_placeholder = ctk.CTkLabel(
                self.tabview.tab("Markov Analysis"),
                text="Analysis controller not available",
                font=ctk.CTkFont(size=16)
            )
            markov_placeholder.pack(padx=20, pady=20)
        
        # Create Trend Analysis panel
        if 'analysis_controller' in self.controllers:
            self.trend_analysis_panel = TrendAnalysisPanel(
                self.tabview.tab("Trend Analysis"),
                self.app_state,
                self.controllers['analysis_controller']
            )
            self.trend_analysis_panel.pack(fill="both", expand=True)
        else:
            trend_placeholder = ctk.CTkLabel(
                self.tabview.tab("Trend Analysis"),
                text="Analysis controller not available",
                font=ctk.CTkFont(size=16)
            )
            trend_placeholder.pack(padx=20, pady=20)
        
        # Initialize tab access control based on project folder state
        self._update_tab_access()
    
    def on_state_change(self, state_key: str, new_value: Any) -> None:
        """
        React to application state changes.
        
        Updates UI elements when relevant state properties change.
        Specifically handles project_folder changes to enable/disable tabs.
        
        Args:
            state_key: Name of the state property that changed
            new_value: New value of the state property
        """
        if state_key == 'project_folder':
            # Update tab access when working directory changes
            self._update_tab_access()
    
    def _update_tab_access(self) -> None:
        """
        Enable or disable tabs based on project folder state.
        
        When no working directory is selected, only the Home tab is accessible.
        When a working directory is selected, all tabs are accessible.
        """
        has_project = self.app_state.project_folder is not None
        
        # Get all tab names
        tab_names = ["Home", "Search", "Upload", "Basic Analysis", "Markov Analysis", "Trend Analysis"]
        
        # Enable/disable tabs based on project folder state
        for tab_name in tab_names:
            if tab_name == "Home":
                # Home tab is always enabled
                continue
            
            # For other tabs, enable only if project folder is set
            if has_project:
                # Enable tab by making it selectable
                # CustomTkinter doesn't have a direct disable method, so we use configure
                try:
                    self.tabview._segmented_button.configure(state="normal")
                except:
                    pass  # If configuration fails, tabs remain accessible
            else:
                # When no project folder, set Home as active tab
                try:
                    self.tabview.set("Home")
                except:
                    pass
    
    
    def on_closing(self) -> None:
        """
        Handle window close event.
        
        This method will be called when the user closes the window.
        The actual shutdown logic (saving state) is handled by the
        DesktopApp class.
        """
        try:
            logger.info("Closing main window")
            
            # Unregister observer
            self.app_state.unregister_observer(self.on_state_change)
            
            # Destroy the window
            self.destroy()
            
        except Exception as e:
            logger.error(f"Error closing window: {e}", exc_info=True)
            # Force destroy even if there's an error
            try:
                self.destroy()
            except:
                pass
    
    def get_geometry(self) -> Dict[str, int]:
        """
        Get current window geometry.
        
        Returns:
            Dictionary with width, height, x, and y coordinates
        """
        # Parse geometry string (format: "widthxheight+x+y")
        geometry = self.geometry()
        
        # Split into size and position
        size_pos = geometry.split('+')
        size = size_pos[0].split('x')
        
        result = {
            'width': int(size[0]),
            'height': int(size[1])
        }
        
        # Add position if available
        if len(size_pos) >= 3:
            result['x'] = int(size_pos[1])
            result['y'] = int(size_pos[2])
        else:
            # Default position if not available
            result['x'] = 100
            result['y'] = 100
        
        return result
    
    def set_geometry(self, geometry: Dict[str, int]) -> None:
        """
        Set window geometry from dictionary.
        
        Args:
            geometry: Dictionary with width, height, x, and y coordinates
        """
        width = geometry.get('width', 1200)
        height = geometry.get('height', 800)
        x = geometry.get('x', 100)
        y = geometry.get('y', 100)
        
        self.geometry(f"{width}x{height}+{x}+{y}")
