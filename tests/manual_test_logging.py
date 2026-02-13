"""
Manual test to verify logging configuration works correctly.

This script tests that:
1. Log directory is created in AppData
2. Log file is created with correct name
3. Log entries are written with correct format
4. Rotating file handler is configured
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from precipgen.core.log_config import setup_logging


def test_logging_configuration():
    """Test logging configuration manually."""
    print("Testing logging configuration...")
    
    # Determine log file location
    if sys.platform == 'win32':
        appdata = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        log_dir = appdata / 'PrecipGen' / 'logs'
    else:
        log_dir = Path.home() / '.precipgen' / 'logs'
    
    log_file = log_dir / 'precipgen_desktop.log'
    
    print(f"Expected log directory: {log_dir}")
    print(f"Expected log file: {log_file}")
    
    # Set up logging
    logger = setup_logging(
        name='precipgen.desktop.test',
        level='INFO',
        log_file=str(log_file),
        console=True,
        max_bytes=10 * 1024 * 1024,  # 10MB
        backup_count=5
    )
    
    # Write test log entries
    logger.info("Test log entry - INFO level")
    logger.warning("Test log entry - WARNING level")
    logger.error("Test log entry - ERROR level")
    
    # Verify log directory exists
    if log_dir.exists():
        print(f"✓ Log directory created: {log_dir}")
    else:
        print(f"✗ Log directory NOT created: {log_dir}")
        return False
    
    # Verify log file exists
    if log_file.exists():
        print(f"✓ Log file created: {log_file}")
    else:
        print(f"✗ Log file NOT created: {log_file}")
        return False
    
    # Read and display log contents
    print("\nLog file contents:")
    print("-" * 80)
    with open(log_file, 'r') as f:
        contents = f.read()
        print(contents)
    print("-" * 80)
    
    # Verify log format
    if 'INFO' in contents and 'WARNING' in contents and 'ERROR' in contents:
        print("✓ Log entries written with correct levels")
    else:
        print("✗ Log entries missing or incorrect")
        return False
    
    if 'precipgen.desktop.test' in contents:
        print("✓ Logger name included in log entries")
    else:
        print("✗ Logger name missing from log entries")
        return False
    
    # Check for timestamp format
    import re
    timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
    if re.search(timestamp_pattern, contents):
        print("✓ Timestamp format correct")
    else:
        print("✗ Timestamp format incorrect")
        return False
    
    # Verify rotating file handler
    from logging.handlers import RotatingFileHandler
    has_rotating = any(isinstance(h, RotatingFileHandler) for h in logger.handlers)
    if has_rotating:
        print("✓ RotatingFileHandler configured")
    else:
        print("✗ RotatingFileHandler NOT configured")
        return False
    
    print("\n✓ All logging tests passed!")
    return True


if __name__ == '__main__':
    try:
        success = test_logging_configuration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
