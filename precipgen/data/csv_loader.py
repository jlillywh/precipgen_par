import pandas as pd
from pathlib import Path

def load_csv(file_path):
    """
    Load a CSV or Excel file and return a DataFrame compatible with PrecipGenPar.
    
    Args:
        file_path: Path to CSV or Excel file
        
    Returns:
        Tuple of (DataFrame, metadata dict)
    """
    file_path = Path(file_path)
    file_ext = file_path.suffix.lower()
    
    # Determine file type and read accordingly
    if file_ext in ['.xlsx', '.xls']:
        # Excel file - read first sheet
        df_raw = pd.read_excel(file_path, sheet_name=0)
        
        # Convert to list of lines for unified processing
        lines = []
        for idx, row in df_raw.iterrows():
            line = ','.join([str(val) for val in row.values])
            lines.append(line + '\n')
    elif file_ext == '.csv':
        # CSV file - read as text
        with open(file_path, 'r') as file:
            lines = file.readlines()
    else:
        raise ValueError(f"Unsupported file type: {file_ext}. Use CSV (.csv) or Excel (.xlsx, .xls)")

    # Extract metadata
    metadata = {}
    data_start_idx = None
    for idx, line in enumerate(lines):
        if line.startswith("DATE"):
            data_start_idx = idx
            break
        else:
            if ',' in line:
                key, value = line.strip().split(',', 1)
                metadata[key] = value
            else:
                metadata[line.strip()] = None

    if data_start_idx is None:
        raise ValueError("File does not contain the expected header row")

    # Read the data into a DataFrame
    if file_ext in ['.xlsx', '.xls']:
        data = pd.read_excel(file_path, sheet_name=0, skiprows=data_start_idx)
    else:
        data = pd.read_csv(file_path, skiprows=data_start_idx)
    
    # Ensure the DataFrame contains 'DATE' and 'PRCP' columns
    if 'DATE' not in data.columns or 'PRCP' not in data.columns:
        raise ValueError("File must contain 'DATE' and 'PRCP' columns")

    # Convert 'DATE' column to datetime
    data['DATE'] = pd.to_datetime(data['DATE'])

    # Add metadata as attributes to the DataFrame
    for key, value in metadata.items():
        data.attrs[key] = value

    return data, metadata