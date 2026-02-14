"""
Tests for standardized CSV writing utilities.
"""

import tempfile
from pathlib import Path
import pandas as pd
import pytest
import importlib.util
import sys
import os

# Import csv_writer module directly without triggering desktop package imports
csv_writer_path = os.path.join(
    os.path.dirname(__file__), 
    '..', 
    'precipgen', 
    'desktop', 
    'utils', 
    'csv_writer.py'
)
spec = importlib.util.spec_from_file_location("csv_writer", csv_writer_path)
csv_writer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(csv_writer)


def test_write_csv_with_dataframe():
    """Test writing a DataFrame to CSV with standardized formatting."""
    # Create test DataFrame
    df = pd.DataFrame({
        'Month': [1, 2, 3],
        'Pww': [0.652, 0.598, 0.543],
        'Pwd': [0.234, 0.198, 0.176],
        'Alpha': [1.523, 1.432, 1.389],
        'Beta': [8.765, 7.892, 7.234]
    })
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = Path(f.name)
    
    try:
        csv_writer.write_csv_file(temp_path, df)
        
        # Read back and verify
        content = temp_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Check header is present
        assert lines[0] == 'Month,Pww,Pwd,Alpha,Beta'
        
        # Check data rows
        assert lines[1].startswith('1,')
        assert lines[2].startswith('2,')
        assert lines[3].startswith('3,')
        
        # Check line endings are LF (no CR)
        assert '\r' not in content
        
    finally:
        temp_path.unlink()


def test_write_csv_with_list_of_rows():
    """Test writing list of rows to CSV with standardized formatting."""
    headers = ['Metric', 'Value']
    data = [
        ['Station', 'GHCN001'],
        ['Start Date', '2020-01-01'],
        ['End Date', '2023-12-31'],
        ['Years on Record', '4']
    ]
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = Path(f.name)
    
    try:
        csv_writer.write_csv_file(temp_path, data, headers=headers)
        
        # Read back and verify
        content = temp_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Check header
        assert lines[0] == 'Metric,Value'
        
        # Check data rows
        assert lines[1] == 'Station,GHCN001'
        assert lines[2] == 'Start Date,2020-01-01'
        assert lines[3] == 'End Date,2023-12-31'
        assert lines[4] == 'Years on Record,4'
        
        # Check line endings are LF (no CR)
        assert '\r' not in content
        
    finally:
        temp_path.unlink()


def test_write_csv_list_without_headers_raises_error():
    """Test that writing list of rows without headers raises ValueError."""
    data = [['value1', 'value2']]
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError, match="Headers must be provided"):
            csv_writer.write_csv_file(temp_path, data)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_csv_delimiter_is_comma():
    """Test that CSV files use comma as delimiter."""
    df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = Path(f.name)
    
    try:
        csv_writer.write_csv_file(temp_path, df)
        
        content = temp_path.read_text(encoding='utf-8')
        
        # Check that commas are used as delimiters
        assert ',' in content
        # Check that other common delimiters are not used
        assert '\t' not in content
        assert ';' not in content
        
    finally:
        temp_path.unlink()


def test_csv_encoding_is_utf8():
    """Test that CSV files use UTF-8 encoding."""
    # Create data with special characters
    df = pd.DataFrame({
        'Name': ['Café', 'Zürich', 'Москва'],
        'Value': [1, 2, 3]
    })
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = Path(f.name)
    
    try:
        csv_writer.write_csv_file(temp_path, df)
        
        # Read back with UTF-8 encoding
        content = temp_path.read_text(encoding='utf-8')
        
        # Verify special characters are preserved
        assert 'Café' in content
        assert 'Zürich' in content
        assert 'Москва' in content
        
    finally:
        temp_path.unlink()
