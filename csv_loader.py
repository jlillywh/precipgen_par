import pandas as pd

def load_csv(file_path):
    """Load the CSV file and return a DataFrame compatible with PrecipGenPar."""
    # Read the CSV file
    with open(file_path, 'r') as file:
        lines = file.readlines()

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
        raise ValueError("CSV file does not contain the expected header row")

    # Read the data into a DataFrame
    data = pd.read_csv(file_path, skiprows=data_start_idx)
    
    # Ensure the DataFrame contains 'DATE' and 'PRCP' columns
    if 'DATE' not in data.columns or 'PRCP' not in data.columns:
        raise ValueError("CSV file must contain 'DATE' and 'PRCP' columns")

    # Convert 'DATE' column to datetime
    data['DATE'] = pd.to_datetime(data['DATE'])

    # Add metadata as attributes to the DataFrame
    for key, value in metadata.items():
        data.attrs[key] = value

    return data, metadata