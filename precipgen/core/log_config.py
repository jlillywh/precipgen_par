"""
Logging configuration module for PrecipGen.

Provides standardized logging setup across CLI and desktop interfaces with support
for both file and console output.
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
        name: Logger name (typically module name)
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_file: Path to log file (optional). If provided, logs to file.
        console: Whether to log to console (default: True)
        max_bytes: Maximum log file size before rotation (default: 10MB)
        backup_count: Number of backup log files to keep (default: 3)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logging('precipgen', level='INFO', log_file='logs/app.log')
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
    
    
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if log_file specified
    if log_file:
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
            
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False
    
    return logger




def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger by name.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    
    Example:
        >>> logger = get_logger('precipgen')
        >>> logger.info("Using existing logger")
    """
    return logging.getLogger(name)
