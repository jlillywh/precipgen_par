"""
Standardized CSV writing utilities for consistent output formatting.

This module provides utilities to ensure all CSV output files follow
consistent formatting conventions across the application.
"""

import csv
from pathlib import Path
from typing import List, Union
import pandas as pd


def write_csv_file(
    output_path: Union[str, Path],
    data: Union[pd.DataFrame, List[List[str]]],
    headers: Union[List[str], None] = None
) -> None:
    """
    Write data to CSV file with standardized formatting.
    
    Ensures consistent formatting across all CSV outputs:
    - Comma delimiter
    - Headers in first row
    - Consistent line endings (LF) across all platforms
    - UTF-8 encoding
    
    Args:
        output_path: Path where CSV should be saved
        data: Either a pandas DataFrame or list of rows (each row is a list of values)
        headers: Column headers (required if data is list of rows, ignored if DataFrame)
        
    Raises:
        ValueError: If data is a list but headers are not provided
        IOError: If file cannot be written
    """
    output_path = Path(output_path)
    
    # Handle DataFrame input
    if isinstance(data, pd.DataFrame):
        # Use pandas to_csv with consistent settings
        data.to_csv(
            output_path,
            index=False,
            sep=',',
            encoding='utf-8',
            lineterminator='\n'  # LF line endings on all platforms
        )
        return
    
    # Handle list of rows input
    if headers is None:
        raise ValueError("Headers must be provided when data is a list of rows")
    
    # Write using csv module with consistent settings
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=',', lineterminator='\n')
        writer.writerow(headers)
        writer.writerows(data)
