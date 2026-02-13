"""
Logging configuration module for PrecipGen.

Provides standardized logging setup across CLI and web interfaces with support
for both file and console output. Auto-detects cloud environments and adapts
logging configuration accordingly.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


def setup_logging(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 3
) -> logging.Logger:
    """
    Setup logging with consistent format across PrecipGen.
    
    Args:
        name: Logger name (typically module name or 'streamlit')
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_file: Path to log file (optional). If provided, logs to file.
        console: Whether to log to console (default: True)
        max_bytes: Maximum log file size before rotation (default: 10MB)
        backup_count: Number of backup log files to keep (default: 3)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logging('streamlit', level='INFO', log_file='logs/app.log')
        >>> logger.info("Application started")
    """
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Set logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Create formatter with consistent format
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Detect cloud environment
    is_cloud = _is_cloud_environment()
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if log_file specified and not in cloud
    if log_file and not is_cloud:
        try:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create rotating file handler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        except (OSError, PermissionError) as e:
            # If file logging fails, log to console only
            logger.warning(f"Could not setup file logging: {e}")
    
    # In cloud environment, warn about file logging limitations
    if log_file and is_cloud:
        logger.info("Cloud environment detected - file logging disabled")
    
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False
    
    return logger


def _is_cloud_environment() -> bool:
    """
    Detect if running in a cloud environment (Streamlit Cloud).
    
    Returns:
        True if running in cloud, False otherwise
    """
    # Check for Streamlit Cloud environment variables
    cloud_indicators = [
        'STREAMLIT_SHARING_MODE',
        'STREAMLIT_SERVER_HEADLESS',
        'STREAMLIT_CLOUD'
    ]
    
    for indicator in cloud_indicators:
        if os.getenv(indicator):
            return True
    
    return False


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger by name.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    
    Example:
        >>> logger = get_logger('streamlit')
        >>> logger.info("Using existing logger")
    """
    return logging.getLogger(name)
