"""
Project controller for folder selection and validation.

This module handles project folder selection, validation, and initialization
of the project directory structure.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Tuple
from tkinter import filedialog

from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.models.session_config import SessionConfig


# Configure logging
logger = logging.getLogger(__name__)


class ProjectController:
    """
    Handles project folder selection and validation.
    
    Coordinates between the UI layer and the application state/session config
    for managing the user's project folder. Validates folder accessibility
    and initializes necessary project structure.
    
    Attributes:
        app_state: Runtime application state
        session_config: Persistent session configuration
    """
    
    def __init__(self, app_state: AppState, session_config: SessionConfig):
        """
        Initialize ProjectController.
        
        Args:
            app_state: AppState instance for runtime state management
            session_config: SessionConfig instance for persistent configuration
        """
        self.app_state = app_state
        self.session_config = session_config
    
    def select_project_folder(self) -> Optional[Path]:
        """
        Open folder dialog and validate selection.
        
        Displays a native Windows folder selection dialog, validates the
        selected folder, and updates both app state and session config
        if the selection is valid.
        
        Returns:
            Path to selected folder if valid, None if cancelled or invalid
        """
        try:
            logger.info("Opening project folder selection dialog")
            
            # Get initial directory from current state or session config
            initial_dir = None
            if self.app_state.project_folder:
                initial_dir = str(self.app_state.project_folder)
            elif self.session_config.project_folder:
                initial_dir = str(self.session_config.project_folder)
            
            # Open native folder selection dialog
            selected_path = filedialog.askdirectory(
                title="Select Project Folder",
                initialdir=initial_dir,
                mustexist=True
            )
            
            # User cancelled the dialog
            if not selected_path:
                logger.info("User cancelled folder selection")
                return None
            
            folder_path = Path(selected_path)
            logger.info(f"User selected folder: {folder_path}")
            
            # Validate the selected folder
            is_valid, error_message = self.validate_folder(folder_path)
            
            if not is_valid:
                # Validation failed - error message will be handled by caller
                logger.warning(f"Folder validation failed: {error_message}")
                return None
            
            # Update app state and session config
            self.app_state.set_project_folder(folder_path)
            self.session_config.project_folder = folder_path
            self.session_config.save()
            
            # Initialize project structure
            self.initialize_project_structure(folder_path)
            
            logger.info(f"Project folder set successfully: {folder_path}")
            return folder_path
            
        except Exception as e:
            logger.error(f"Error selecting project folder: {e}", exc_info=True)
            return None
    
    def validate_folder(self, path: Path) -> Tuple[bool, Optional[str]]:
        """
        Check if folder is writable and accessible.
        
        Validates that the path exists, is a directory, and has write
        permissions for the current user.
        
        Args:
            path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if folder is valid, False otherwise
            - error_message: Description of validation failure, None if valid
        """
        try:
            # Check if path exists
            if not path.exists():
                error_msg = f"The selected folder does not exist:\n{path}"
                logger.warning(f"Validation failed: {error_msg}")
                return False, error_msg
            
            # Check if path is a directory
            if not path.is_dir():
                error_msg = f"The selected path is not a folder:\n{path}"
                logger.warning(f"Validation failed: {error_msg}")
                return False, error_msg
            
            # Check if directory is accessible (try to list contents)
            try:
                list(path.iterdir())
            except PermissionError:
                error_msg = f"Permission denied. Cannot access folder:\n{path}\n\nPlease select a folder you have access to."
                logger.warning(f"Validation failed: {error_msg}")
                return False, error_msg
            except OSError as e:
                error_msg = f"Cannot access folder:\n{path}\n\nError: {str(e)}"
                logger.warning(f"Validation failed: {error_msg}")
                return False, error_msg
            
            # Check if directory is writable
            if not os.access(path, os.W_OK):
                error_msg = f"The selected folder is not writable:\n{path}\n\nPlease select a folder you have write permissions for."
                logger.warning(f"Validation failed: {error_msg}")
                return False, error_msg
            
            # All checks passed
            logger.info(f"Folder validation passed: {path}")
            return True, None
            
        except Exception as e:
            error_msg = f"Error validating folder:\n{path}\n\nError: {str(e)}"
            logger.error(f"Unexpected error during folder validation: {e}", exc_info=True)
            return False, error_msg
    
    def initialize_project_structure(self, path: Path) -> None:
        """
        Create necessary subdirectories in project folder.
        
        Sets up the standard project directory structure for storing
        downloaded data, calculated parameters, and exported results.
        
        Args:
            path: Project folder path
        """
        try:
            logger.info(f"Initializing project structure in: {path}")
            
            # Define standard subdirectories
            subdirs = [
                'data',      # Downloaded GHCN data
                'params',    # Calculated and exported parameters
                'exports',   # Final exported parameter files
            ]
            
            # Create subdirectories if they don't exist
            for subdir in subdirs:
                subdir_path = path / subdir
                subdir_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created/verified subdirectory: {subdir_path}")
            
            logger.info("Project structure initialized successfully")
            
        except PermissionError as e:
            logger.error(f"Permission denied creating project structure: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error initializing project structure: {e}", exc_info=True)
            raise
