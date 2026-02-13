"""
Main application entry point for PrecipGen Desktop.

This module provides the DesktopApp class that coordinates all components
and manages the application lifecycle.
"""

import sys
import logging
import os
from pathlib import Path
from typing import Optional

from precipgen.core.log_config import setup_logging
from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.models.session_config import SessionConfig
from precipgen.desktop.controllers.project_controller import ProjectController
from precipgen.desktop.views.main_window import MainWindow


# Configure logging
logger = logging.getLogger(__name__)


class DesktopApp:
    """
    Main application class coordinating all components.
    
    Manages the application lifecycle including initialization,
    session state persistence, and clean shutdown.
    
    Attributes:
        session_config: Persistent session configuration
        app_state: Runtime application state
        main_window: Main application window
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the desktop application.
        
        Args:
            config_path: Optional custom path for session config file
        """
        try:
            # Set up application logging
            self._setup_logging()
            
            logger.info("Initializing PrecipGen Desktop Application")
            
            # Load session configuration
            self.session_config = SessionConfig.load(config_path)
            
            # Initialize application state
            self.app_state = AppState()
            
            # Initialize controllers
            self.project_controller = ProjectController(self.app_state, self.session_config)
            
            # Restore project folder from session if valid
            if self.session_config.validate_project_folder():
                self.app_state.set_project_folder(self.session_config.project_folder)
                logger.info(f"Restored project folder: {self.session_config.project_folder}")
            
            # Initialize main window (will be created in run())
            self.main_window: Optional[MainWindow] = None
            
            logger.info("Application initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}", exc_info=True)
            raise
    
    def _setup_logging(self) -> None:
        """
        Set up application logging with rotating file handler.
        
        Configures logging to write to AppData directory with automatic
        rotation when files reach size limit.
        """
        try:
            # Determine log file location in AppData
            if sys.platform == 'win32':
                appdata = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
                log_dir = appdata / 'PrecipGen' / 'logs'
            else:
                log_dir = Path.home() / '.precipgen' / 'logs'
            
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / 'precipgen_desktop.log'
            
            # Set up logging with rotating file handler
            setup_logging(
                name='precipgen',
                level='INFO',
                log_file=str(log_file),
                console=True,
                max_bytes=10 * 1024 * 1024,  # 10MB
                backup_count=5
            )
            
            # Also set up logging for desktop module
            setup_logging(
                name='precipgen.desktop',
                level='INFO',
                log_file=str(log_file),
                console=True,
                max_bytes=10 * 1024 * 1024,
                backup_count=5
            )
            
            logger.info(f"Logging configured: {log_file}")
            
        except Exception as e:
            # If logging setup fails, print to console and continue
            print(f"Warning: Could not setup logging: {e}", file=sys.stderr)
    
    def run(self) -> None:
        """
        Initialize and start the application.
        
        Creates the main window, restores window geometry from session,
        and starts the CustomTkinter event loop.
        """
        try:
            logger.info("Starting application")
            
            # Create controllers dictionary
            controllers = {
                'project_controller': self.project_controller
            }
            
            # Create main window with controllers
            self.main_window = MainWindow(self.app_state, controllers=controllers)
            
            # Restore window geometry from session
            self.main_window.set_geometry(self.session_config.window_geometry)
            
            # Override the window close handler to call our shutdown method
            self.main_window.protocol("WM_DELETE_WINDOW", self.shutdown)
            
            logger.info("Application window created, starting event loop")
            
            # Start the event loop
            self.main_window.mainloop()
            
        except Exception as e:
            logger.error(f"Error running application: {e}", exc_info=True)
            # Show error dialog if possible
            try:
                import tkinter.messagebox as messagebox
                messagebox.showerror(
                    "Application Error",
                    f"An error occurred while running the application:\n\n{str(e)}\n\n"
                    f"Please check the log file for details."
                )
            except:
                pass
            raise
    
    def shutdown(self) -> None:
        """
        Clean shutdown with state persistence.
        
        Saves session configuration including current project folder
        and window geometry before closing the application.
        """
        try:
            logger.info("Shutting down application")
            
            if self.main_window is not None:
                # Save current window geometry
                self.session_config.window_geometry = self.main_window.get_geometry()
                
                # Save current project folder
                self.session_config.project_folder = self.app_state.project_folder
                
                # Persist configuration to disk
                try:
                    self.session_config.save()
                    logger.info("Session configuration saved")
                except Exception as e:
                    logger.error(f"Could not save session configuration: {e}", exc_info=True)
                    print(f"Warning: Could not save session configuration: {e}")
                
                # Close the window
                self.main_window.on_closing()
            
            logger.info("Application shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
            # Continue with shutdown even if there's an error
            if self.main_window is not None:
                try:
                    self.main_window.destroy()
                except:
                    pass


def main():
    """
    Main entry point for the PrecipGen Desktop application.
    
    Creates and runs the DesktopApp instance with top-level error handling.
    """
    try:
        app = DesktopApp()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        logging.error(f"Fatal error in main: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
