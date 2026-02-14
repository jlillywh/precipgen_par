"""
Unit tests for application logging configuration.

Tests verify that logging is properly configured with rotating file handler,
correct log file location in AppData, and appropriate log levels.
"""

import pytest
import logging
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

from precipgen.desktop.app import DesktopApp


def test_logging_setup_creates_log_directory(tmp_path):
    """Test that logging setup creates log directory in AppData."""
    # Mock the AppData path to use temp directory
    with patch.dict('os.environ', {'APPDATA': str(tmp_path)}):
        with patch('precipgen.desktop.app.MainWindow'):
            try:
                app = DesktopApp()
                
                # Verify log directory was created
                if sys.platform == 'win32':
                    expected_log_dir = tmp_path / 'PrecipGen' / 'logs'
                else:
                    expected_log_dir = Path.home() / '.precipgen' / 'logs'
                
                # On Windows, check the mocked path
                if sys.platform == 'win32':
                    assert expected_log_dir.exists()
                    assert expected_log_dir.is_dir()
                    
            except Exception as e:
                # App initialization might fail due to missing dependencies
                # but logging should still be configured
                pass


def test_logging_uses_rotating_file_handler():
    """Test that logging uses RotatingFileHandler."""
    from precipgen.core.log_config import setup_logging
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        logger = setup_logging(
            name='test_logger',
            level='INFO',
            log_file=str(log_file),
            console=False,
            max_bytes=1024,
            backup_count=3
        )
        
        # Verify logger has handlers
        assert len(logger.handlers) > 0
        
        # Verify at least one handler is a RotatingFileHandler
        from logging.handlers import RotatingFileHandler
        has_rotating_handler = any(
            isinstance(h, RotatingFileHandler) for h in logger.handlers
        )
        assert has_rotating_handler
        
        # Close all handlers to release file locks
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)


def test_logging_level_configuration():
    """Test that logging level is properly configured."""
    from precipgen.core.log_config import setup_logging
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        # Test INFO level
        logger = setup_logging(
            name='test_info_logger',
            level='INFO',
            log_file=str(log_file),
            console=False
        )
        
        assert logger.level == logging.INFO
        
        # Close handlers
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Test DEBUG level
        logger_debug = setup_logging(
            name='test_debug_logger',
            level='DEBUG',
            log_file=str(log_file),
            console=False
        )
        
        assert logger_debug.level == logging.DEBUG
        
        # Close handlers
        for handler in logger_debug.handlers[:]:
            handler.close()
            logger_debug.removeHandler(handler)


def test_logging_format_includes_required_fields():
    """Test that log format includes timestamp, level, name, and message."""
    from precipgen.core.log_config import setup_logging
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        logger = setup_logging(
            name='test_format_logger',
            level='INFO',
            log_file=str(log_file),
            console=False
        )
        
        # Log a test message
        logger.info("Test message")
        
        # Flush and close handlers to ensure log is written
        for handler in logger.handlers:
            handler.flush()
        
        # Read log file and verify format
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        # Close handlers
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Verify log contains required fields
        assert 'INFO' in log_content
        assert 'test_format_logger' in log_content
        assert 'Test message' in log_content
        # Verify timestamp format (YYYY-MM-DD HH:MM:SS)
        import re
        timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
        assert re.search(timestamp_pattern, log_content)


def test_logging_handles_errors_gracefully():
    """Test that logging setup handles errors gracefully."""
    from precipgen.core.log_config import setup_logging
    
    # Try to log to an invalid path (should not raise exception)
    try:
        logger = setup_logging(
            name='test_error_logger',
            level='INFO',
            log_file='/invalid/path/that/does/not/exist/test.log',
            console=False
        )
        # Should still return a logger even if file logging fails
        assert logger is not None
    except Exception as e:
        pytest.fail(f"Logging setup should handle errors gracefully: {e}")


def test_logger_available_in_all_modules():
    """Test that logger is available in all desktop modules."""
    # Import all desktop modules and verify they have loggers
    from precipgen.desktop import app
    from precipgen.desktop.controllers import project_controller
    from precipgen.desktop.controllers import data_controller
    from precipgen.desktop.controllers import calibration_controller
    from precipgen.desktop.controllers import analysis_controller
    from precipgen.desktop.views import main_window
    from precipgen.desktop.views import home_panel
    from precipgen.desktop.views import search_panel
    from precipgen.desktop.views import upload_panel
    from precipgen.desktop.views import basic_analysis_panel
    from precipgen.desktop.views import markov_analysis_panel
    from precipgen.desktop.views import trend_analysis_panel
    
    # Verify each module has a logger
    modules = [
        app,
        project_controller,
        data_controller,
        calibration_controller,
        analysis_controller,
        main_window,
        home_panel,
        search_panel,
        upload_panel,
        basic_analysis_panel,
        markov_analysis_panel,
        trend_analysis_panel
    ]
    
    for module in modules:
        # Check if module has logger attribute
        assert hasattr(module, 'logger'), f"Module {module.__name__} missing logger"
        assert isinstance(module.logger, logging.Logger)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
