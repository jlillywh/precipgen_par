"""
Main application window for PrecipGen Desktop.

This module provides the top-level window with basic layout structure.
"""

import logging
import customtkinter as ctk
from typing import Any, Dict, Optional
from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.views.project_panel import ProjectPanel


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
        
        Creates the layout structure with ProjectPanel for folder management
        and a main content area for future panels.
        """
        # Configure grid layout (2 rows, 1 column)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create ProjectPanel for project folder management
        # Only create if we have a project_controller
        if 'project_controller' in self.controllers:
            self.project_panel = ProjectPanel(
                self,
                self.controllers['project_controller'],
                self.app_state
            )
            self.project_panel.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        else:
            # Fallback to basic header if controller not available
            self.header_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
            self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
            self.header_frame.grid_columnconfigure(0, weight=1)
            
            self.project_label = ctk.CTkLabel(
                self.header_frame,
                text="Project: No project folder selected",
                font=ctk.CTkFont(size=14)
            )
            self.project_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        # Create main content frame
        self.content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Placeholder label for content area
        self.placeholder_label = ctk.CTkLabel(
            self.content_frame,
            text="PrecipGen Desktop Application\n\nData and Calibration panels will be added in future phases.",
            font=ctk.CTkFont(size=16)
        )
        self.placeholder_label.grid(row=0, column=0, padx=20, pady=20)
    
    def on_state_change(self, state_key: str, new_value: Any) -> None:
        """
        React to application state changes.
        
        Updates UI elements when relevant state properties change.
        ProjectPanel handles its own state updates, so this is mainly
        for future panels.
        
        Args:
            state_key: Name of the state property that changed
            new_value: New value of the state property
        """
        # ProjectPanel handles project_folder updates itself
        # Future panels will handle their own state updates here
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
