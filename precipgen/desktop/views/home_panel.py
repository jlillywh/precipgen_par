"""
Home panel view component for PrecipGen Desktop.

This module provides the UI for session initialization, including
application title, description, and working directory selection.
"""

import logging
import customtkinter as ctk
from pathlib import Path
from typing import Optional
from tkinter import messagebox

from precipgen.desktop.controllers.project_controller import ProjectController
from precipgen.desktop.models.app_state import AppState


# Configure logging
logger = logging.getLogger(__name__)


class HomePanel(ctk.CTkFrame):
    """
    UI component for session initialization and working directory selection.
    
    Provides application title, description, and folder selection interface.
    Integrates with ProjectController for folder validation and management.
    
    Attributes:
        project_controller: Controller for project folder operations
        app_state: Application state manager
        title_label: Label displaying application title
        description_label: Label displaying tool description
        folder_label: Label displaying current project folder path
        change_button: Button to trigger folder selection dialog
    """
    
    def __init__(self, parent, project_controller: ProjectController, app_state: AppState):
        """
        Initialize HomePanel.
        
        Args:
            parent: Parent widget (typically MainWindow)
            project_controller: ProjectController instance for folder operations
            app_state: AppState instance for observing state changes
        """
        super().__init__(parent, corner_radius=0)
        
        self.project_controller = project_controller
        self.app_state = app_state
        
        # Setup the panel layout
        self.setup_ui()
        
        # Register as observer for state changes
        self.app_state.register_observer(self.on_state_change)
        
        # Initialize display with current state
        self.update_folder_display(self.app_state.project_folder)
    
    def setup_ui(self) -> None:
        """
        Configure the panel layout and widgets.
        
        Creates a vertical layout with application title, description,
        and working directory selector.
        """
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        
        # Application title
        self.title_label = ctk.CTkLabel(
            self,
            text="PrecipGen Parameter Analyzer",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w"
        )
        self.title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 5), sticky="w")
        
        # Application description
        self.description_label = ctk.CTkLabel(
            self,
            text="Analyze daily precipitation time series and generate parameters for stochastic simulation",
            font=ctk.CTkFont(size=12),
            anchor="w",
            text_color="gray"
        )
        self.description_label.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 15), sticky="w")
        
        # Project folder label
        self.folder_label = ctk.CTkLabel(
            self,
            text="Working Directory: No directory selected",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        self.folder_label.grid(row=2, column=0, padx=20, pady=15, sticky="w")
        
        # Change folder button
        self.change_button = ctk.CTkButton(
            self,
            text="Select Directory...",
            width=150,
            command=self.on_change_folder_clicked
        )
        self.change_button.grid(row=2, column=1, padx=20, pady=15, sticky="e")
    
        # Recent Projects Section
        self.recent_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.recent_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=(20, 0), sticky="nsew")
        self.recent_frame.grid_columnconfigure(0, weight=1)
        
        self.recent_label = ctk.CTkLabel(
            self.recent_frame,
            text="Recent Projects",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        self.recent_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # Container for recent project buttons
        self.recent_list_frame = ctk.CTkFrame(self.recent_frame, fg_color="transparent")
        self.recent_list_frame.grid(row=1, column=0, sticky="nsew")
        self.recent_list_frame.grid_columnconfigure(0, weight=1)
        
        self.update_recent_projects()

    def update_recent_projects(self) -> None:
        """
        Refresh the list of recent projects.
        """
        # Clear existing buttons
        for widget in self.recent_list_frame.winfo_children():
            widget.destroy()
            
        recent_paths = self.project_controller.session_config.recent_projects
        
        if not recent_paths:
            no_recent = ctk.CTkLabel(
                self.recent_list_frame,
                text="No recent projects",
                text_color="gray",
                anchor="w"
            )
            no_recent.grid(row=0, column=0, sticky="w")
            return
            
        for i, path_str in enumerate(recent_paths):
            path = Path(path_str)
            btn = ctk.CTkButton(
                self.recent_list_frame,
                text=str(path),
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda p=path: self.on_recent_project_clicked(p)
            )
            btn.grid(row=i, column=0, sticky="ew", pady=2)
            
    def on_recent_project_clicked(self, path: Path) -> None:
        """
        Handle click on a recent project.
        
        Args:
            path: Path to the project folder
        """
        if self.project_controller.load_project_folder(path):
            messagebox.showinfo(
                "Project Loaded",
                f"Loaded project:\n{path}"
            )
        else:
            messagebox.showerror(
                "Error",
                f"Could not load project:\n{path}\n\nThe folder may no longer exist or be accessible."
            )
            # Refresh list to potentially remove invalid entry (handled by add_recent_project in controller logic if we wanted to be strict, but for now just refresh UI if needed)
            self.update_recent_projects()
    
    def on_change_folder_clicked(self) -> None:
        """
        Handle folder change button click.
        
        Opens the folder selection dialog via ProjectController and
        displays appropriate feedback to the user.
        """
        try:
            logger.info("User clicked change folder button")
            
            # Attempt to select a new project folder
            selected_folder = self.project_controller.select_project_folder()
            
            if selected_folder is None:
                # User cancelled or validation failed
                # Check if there was a validation error
                logger.info("Folder selection cancelled or failed")
                return
            
            # Success - folder display will be updated via state observer
            # Show confirmation message
            logger.info(f"Working directory selected: {selected_folder}")
            messagebox.showinfo(
                "Working Directory Selected",
                f"Working directory set to:\n{selected_folder}"
            )
            
            # Update recent projects list
            self.update_recent_projects()
            
        except Exception as e:
            logger.error(f"Error changing working directory: {e}", exc_info=True)
            messagebox.showerror(
                "Error",
                f"An error occurred while changing the working directory:\n\n{str(e)}\n\n"
                f"Please check the log file for more information."
            )
    
    def update_folder_display(self, folder_path: Optional[Path]) -> None:
        """
        Update UI to show current working directory.
        
        Updates the label text to display the current working directory path,
        or a default message if no directory is selected.
        
        Args:
            folder_path: Path to the working directory, or None if no directory selected
        """
        if folder_path is None:
            self.folder_label.configure(text="Working Directory: No directory selected")
        else:
            # Display the full path
            self.folder_label.configure(text=f"Working Directory: {folder_path}")
            
        # Also refresh recent projects as the order might have changed
        # (defer this to ensure config is saved first)
        self.after(100, self.update_recent_projects)
    
    def on_state_change(self, state_key: str, new_value) -> None:
        """
        React to application state changes.
        
        Updates the folder display when the project folder changes.
        
        Args:
            state_key: Name of the state property that changed
            new_value: New value of the state property
        """
        if state_key == 'project_folder':
            self.update_folder_display(new_value)
        elif state_key == 'clear_all':
            self.update_folder_display(None)
    
    def destroy(self) -> None:
        """
        Clean up resources when panel is destroyed.
        
        Unregisters the state observer before destroying the widget.
        """
        # Unregister observer
        self.app_state.unregister_observer(self.on_state_change)
        
        # Call parent destroy
        super().destroy()
