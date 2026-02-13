"""
Session configuration management for PrecipGen Desktop.

This module handles persistent storage of user session state including
project folder paths and window geometry.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class SessionConfig:
    """
    Manages persistent session state across application runs.
    
    Configuration is stored in JSON format in the user's AppData directory.
    Validates project folder paths on load to ensure they remain accessible.
    
    Attributes:
        config_path: Path to the configuration file
        project_folder: Currently selected project folder path
        window_geometry: Dictionary containing window dimensions and position
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize SessionConfig with optional custom config path.
        
        Args:
            config_path: Optional custom path for config file.
                        If None, uses default AppData location.
        """
        if config_path is None:
            # Use AppData directory on Windows
            appdata = os.getenv('APPDATA')
            if appdata:
                config_dir = Path(appdata) / 'PrecipGen'
            else:
                # Fallback to user home directory
                config_dir = Path.home() / '.precipgen'
            
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / 'session_config.json'
        else:
            self.config_path = config_path
            
        self.project_folder: Optional[Path] = None
        self.window_geometry: Dict[str, int] = {
            'width': 1200,
            'height': 800,
            'x': 100,
            'y': 100
        }
        self._last_used: Optional[str] = None
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'SessionConfig':
        """
        Load configuration from disk.
        
        Creates a new default configuration if the file doesn't exist
        or cannot be parsed.
        
        Args:
            config_path: Optional custom path for config file
            
        Returns:
            SessionConfig instance with loaded or default values
        """
        config = cls(config_path)
        
        if not config.config_path.exists():
            return config
        
        try:
            with open(config.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load project folder if present
            if 'project_folder' in data and data['project_folder']:
                config.project_folder = Path(data['project_folder'])
            
            # Load window geometry if present
            if 'window_geometry' in data:
                config.window_geometry.update(data['window_geometry'])
            
            # Load last used timestamp
            if 'last_used' in data:
                config._last_used = data['last_used']
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # If config is corrupted, return default config
            # Log the error but don't fail
            print(f"Warning: Could not load config from {config.config_path}: {e}")
            return config
        
        return config
    
    def save(self) -> None:
        """
        Persist configuration to disk.
        
        Saves current project folder, window geometry, and timestamp
        to the configuration file in JSON format.
        
        Raises:
            OSError: If the config file cannot be written
        """
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'project_folder': str(self.project_folder) if self.project_folder else None,
            'window_geometry': self.window_geometry,
            'last_used': datetime.now().isoformat()
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def validate_project_folder(self) -> bool:
        """
        Check if stored project folder is still valid.
        
        Validates that the project folder exists and is accessible.
        If validation fails, clears the project folder path.
        
        Returns:
            True if project folder is valid and accessible, False otherwise
        """
        if self.project_folder is None:
            return False
        
        try:
            # Check if path exists
            if not self.project_folder.exists():
                self.project_folder = None
                return False
            
            # Check if path is a directory
            if not self.project_folder.is_dir():
                self.project_folder = None
                return False
            
            # Check if directory is accessible (try to list contents)
            list(self.project_folder.iterdir())
            
            return True
            
        except (OSError, PermissionError):
            # Path exists but is not accessible
            self.project_folder = None
            return False
