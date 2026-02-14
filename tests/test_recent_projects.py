
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from precipgen.desktop.models.session_config import SessionConfig
from precipgen.desktop.models.app_state import AppState
from precipgen.desktop.controllers.project_controller import ProjectController

class TestRecentProjects(unittest.TestCase):
    """Test suite for Recent Projects feature."""
    
    def setUp(self):
        # Create a temporary directory for config and projects
        self.test_dir = tempfile.mkdtemp()
        self.config_path = Path(self.test_dir) / "config.json"
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def test_session_config_add_recent(self):
        """Test adding recent projects to SessionConfig."""
        config = SessionConfig(self.config_path)
        
        # Add first project
        p1 = Path(self.test_dir) / "project1"
        config.add_recent_project(p1)
        
        self.assertEqual(len(config.recent_projects), 1)
        self.assertEqual(config.recent_projects[0], str(p1))
        
        # Add second project
        p2 = Path(self.test_dir) / "project2"
        config.add_recent_project(p2)
        
        self.assertEqual(len(config.recent_projects), 2)
        self.assertEqual(config.recent_projects[0], str(p2))
        self.assertEqual(config.recent_projects[1], str(p1))
        
        # Add proper duplicate (p1) -> should move to top
        config.add_recent_project(p1)
        
        self.assertEqual(len(config.recent_projects), 2)
        self.assertEqual(config.recent_projects[0], str(p1))
        self.assertEqual(config.recent_projects[1], str(p2))
        
    def test_session_config_limit(self):
        """Test that recent projects list is limited to 5."""
        config = SessionConfig(self.config_path)
        
        # Add 6 projects
        for i in range(6):
            p = Path(self.test_dir) / f"project{i}"
            config.add_recent_project(p)
            
        self.assertEqual(len(config.recent_projects), 5)
        # Most recent should be project5
        self.assertEqual(config.recent_projects[0], str(Path(self.test_dir) / "project5"))
        # Oldest should be project1 (project0 fell off)
        self.assertEqual(config.recent_projects[-1], str(Path(self.test_dir) / "project1"))
        
    def test_persistence(self):
        """Test that recent projects are saved and loaded."""
        config = SessionConfig(self.config_path)
        p1 = Path(self.test_dir) / "project1"
        config.add_recent_project(p1)
        
        # create new instance loading from same path
        loaded_config = SessionConfig.load(self.config_path)
        
        self.assertEqual(len(loaded_config.recent_projects), 1)
        self.assertEqual(loaded_config.recent_projects[0], str(p1))

    def test_controller_integration(self):
        """Test ProjectController updates recent projects."""
        app_state = AppState()
        session_config = SessionConfig(self.config_path)
        controller = ProjectController(app_state, session_config)
        
        # Create a valid project folder
        project_dir = Path(self.test_dir) / "valid_project"
        project_dir.mkdir()
        
        # Mock file dialog to return this path
        with patch('tkinter.filedialog.askdirectory', return_value=str(project_dir)):
            controller.select_project_folder()
            
        # Verify it was added to recent projects
        self.assertIn(str(project_dir), session_config.recent_projects)
        
        # Test loading directly via load_project_folder
        project_dir_2 = Path(self.test_dir) / "valid_project_2"
        project_dir_2.mkdir()
        
        result = controller.load_project_folder(project_dir_2)
        
        self.assertTrue(result)
        self.assertEqual(app_state.project_folder, project_dir_2)
        self.assertEqual(session_config.recent_projects[0], str(project_dir_2))

if __name__ == '__main__':
    unittest.main()
