# PrecipGen Parameter Generator

## 1. Introduction
The `PrecipGenPAR` program produces the input parameters needed to run a stochastic precipitation simulator called "PrecipGen." PrecipGen is a first-order, 2-state Markov chain-gamma model that simulates daily precipitation for a long-term simulation at a single point on the earth. A Markov process models the change between 2 states (wet vs dry) randomly over time and the probability of a state change depends on the previous state. Precipitation rate is modeled by sampling from a gamma probability distribution. Leveraging the foundational work of Dee Allen Wright and the WGEN model from 1983, implemented in FORTRAN, this program inherits a legacy of reliability in precipitation simulation. This implementation has the added option to incorporate long-term cyclic behavior, based correlations found in the historical record.

## 2. Design
The system consists of two main components: the Parameter Calculator "PrecipGenPAR" and the Precipitation Simulator "PrecipGen".

### 2.1 PrecipGenPAR
Reads long-term historical record and calculates four parameters for each month. It also calculates these parameters based on identified dry and deluge periods (long-term capability is phase 2).

#### 2.2 PrecipGen
This component runs a simulation using the precip generator, a Markov chain model, with the parameters provided by the Parameter Calculator. In phase 2, incorporate long-term logic.

## 3. Getting Started
The workflow for using the `PrecipGen` project involves several steps:

### 3.1 Establish the Time Series (Not Included in Design)
The first step is to establish a time series of daily precipitation totals over a long-term history. This data can usually be downloaded from the NOAA NCEI webpage. Ensure that the data is clean and ready to be used, and follows our requirements for the time series. Assume this is done outside of PrecipGen!

### 3.2 Fill Missing Data (RECOMMENDED)
Real-world precipitation data often contains missing values. Use the professional-grade data filling module to handle gaps:

- **Linear interpolation**: For 1-2 day gaps
- **Climatological normals**: For 3-7 day gaps using seasonal averages from other years
- **Analogous year method**: For 8+ day gaps using meteorologically similar years

The data filler follows best practices used by professional hydrologists and meteorologists, including statistical validation and quality control.

### 3.3 Run PrecipGenPAR
Once you have the time series (preferably with missing data filled), you can run the preprocessor, `PrecipGenPAR`. This requires a configuration file that points to a CSV file containing the daily precipitation data. When you run `PrecipGenPAR`, you need to load the time series. The JSON file should have a reference to the path to this file.

### 3.4 Generate Input Parameters
After initializing a new simulation, use a function in `PrecipGenPAR` to generate the input parameters. These parameters will be used as input to `PrecipGen`.

### 3.5 Execute a Simulation
To execute a simulation, you need the start and end dates, which are defined in the JSON file. The simulation starts on the start date and walks forward in time one day at a time. During each update, `PrecipGen` calculates a new output, which is the rainfall for the day. This continues until the end date is reached.

### 3.6 Results
When the simulation is complete, the results are stored in a text file as a time series of daily precipitation over the long term. Another text file contains annual and monthly totals and statistics.

## 4. Usage

### 4.1 Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/yourusername/PrecipGenPAR.git
    cd PrecipGenPAR
    ```

2. **Create a virtual environment:**

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

## Quick Start for New Users

### For Beginners - Easy Menu Interface

If you're new to command line tools, use the easy menu interface:

**Windows:**
```cmd
# Double-click start_precipgen.bat
# OR run in command prompt:
python easy_start.py
```

**Mac/Linux:**
```bash
# Make executable and run:
chmod +x start_precipgen.sh
./start_precipgen.sh
# OR run directly:
python3 easy_start.py
```

This will give you a simple menu to:
1. Check data quality
2. Calculate parameters  
3. Run wave analysis
4. Get help finding weather data

### For Command Line Users

See the [Getting Started Guide](GETTING_STARTED.md) for detailed command line instructions.

### First Time Setup

1. **Install Python 3.8+** from https://python.org
2. **Download this tool** from GitHub
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Get weather data** from https://www.ncdc.noaa.gov/cdo-web/
5. **Run analysis**: Use `python easy_start.py` or command line tools

### Example Workflow

```bash
# Easy way - menu interface
python easy_start.py

# Command line way
python cli.py download-station USW00023066 -o data.csv
python cli.py fill-data data.csv -o filled_data.csv  # NEW: Fill missing values
python cli.py gap-analysis filled_data.csv -o gaps.csv
python cli.py params filled_data.csv -o parameters.csv  
python cli.py wave-analysis filled_data.csv --create-plots --project-years 20
```

### 4.2 Running the PrecipGenPAR Script

1. **Run the script:**

    ```sh
    python pgpar_cmd.py
    ```

2. **Follow the prompts:**

    - Enter the GHCN station ID when prompted.

3. **View the results:**

    - The script will fetch and process the data, then save the results to a CSV file named `<station_id>_precipitation_parameters.csv`.

### 4.3 Example

```sh
$ python pgpar_cmd.py
Enter the GHCN station ID: USW00094728
Fetching data for station USW00094728...
Dataset Summary:
Station Name: NEW YORK CENTRAL PARK, NY US
Station ID: USW00094728
Location: NY
Coordinates: 40.779, -73.969
Elevation: 42.1 meters
Precipitation units: inches
Date Range: 01/01/2020 to 12/31/2020
Total Records: 366
Precipitation Stats:
  Average Annual Precipitation: 49.92 inches
  Mean Daily Precipitation: 0.14 inches
  Standard Deviation: 0.34 inches

Annual Precipitation Autocorrelation:
  Autocorrelation: 0.1234
  Optimal Lag: 1 year(s)

Results saved to USW00094728_precipitation_parameters.csv
```

### 4.4 Wave Analysis of Parameter Evolution

The system includes advanced wave function analysis to characterize the temporal evolution of PrecipGen parameters. This analysis identifies cyclic patterns and trends in PWW, PWD, alpha, and beta over time.

#### Usage:

```sh
# Basic wave analysis
python cli.py wave-analysis input_data.csv -o wave_results

# Advanced wave analysis with custom parameters
python cli.py wave-analysis input_data.csv \
  --window-years 10 \
  --overlap 0.5 \
  --num-components 5 \
  --create-plots \
  --project-years 20 \
  -o wave_analysis_output

# Demo script for comprehensive analysis
python demo_pgpar_wave.py
```

#### Parameters:
- `--window-years`: Size of sliding window in years (default: 10)
- `--overlap`: Window overlap fraction (default: 0.5)
- `--num-components`: Number of wave components to extract (default: 5)
- `--min-data-threshold`: Minimum data coverage per window (default: 0.8)
- `--project-years`: Years to project into future (default: 0)
- `--create-plots`: Generate visualization plots

#### Output Files:
- `*_wave_params.json`: Complete wave function parameters
- `*_components.csv`: Summary of wave components
- `*_history.csv`: Parameter values over time
- `*_projections.csv`: Future parameter projections (if requested)
- `*_evolution.png`: Parameter evolution plots (if requested)
- `*_components.png`: Wave component analysis plots (if requested)

#### Example Output:
```
Analysis Summary:
--------------------------------------------------

PWW:
  Trend: -0.000326 per year
  Dominant period: 8.0 years
  Total wave amplitude: 0.1821
  Components: 0 short-term, 1 medium-term, 0 long-term

PWD:
  Trend: -0.000028 per year
  Dominant period: 8.0 years
  Total wave amplitude: 0.0637
  Components: 1 short-term, 1 medium-term, 0 long-term
```

### 4.5 Data Filling for Missing Values

Real-world precipitation data often contains missing values due to equipment failures, maintenance periods, or data transmission issues. The PrecipGen PAR tool includes professional-grade data filling capabilities that follow meteorological best practices.

#### Usage:

```sh
# Basic data filling
python cli.py fill-data input_data.csv -o filled_data.csv

# Advanced options
python cli.py fill-data input_data.csv \
  --max-gap-days 30 \
  --min-similarity 0.7 \
  --seasonal-window 15 \
  --min-years-climatology 10 \
  -o filled_data.csv
```

#### Filling Methods:

1. **Linear Interpolation (1-2 day gaps)**
   - Simple linear interpolation between adjacent values
   - Most appropriate for very short gaps
   - Ensures smooth transitions

2. **Climatological Normal (3-7 day gaps)**
   - Uses seasonal averages from other years
   - Considers ±15 day window around target date
   - Preserves seasonal patterns

3. **Analogous Year Method (8+ day gaps)**
   - Finds meteorologically similar years
   - Based on seasonal precipitation patterns
   - Uses correlation analysis for year selection

#### Quality Control:

- Statistical validation of filled values
- Preservation of seasonal patterns
- No negative precipitation values
- Extreme value detection
- Comprehensive quality report generation

#### Output Files:

- `*_filled.csv`: Data with missing values filled
- `*_filling_report.json`: Detailed filling statistics and validation

#### Example Output:
```
Data Filling Summary:
Original missing values: 45
Final missing values: 3
Values filled: 42
Success rate: 93.3%

Methods used:
  Linear Interpolation: 8
  Climatological Normal: 6  
  Analogous Year: 4
```

## 5. Testing
The `PrecipGen` project includes a suite of tests to verify its functionality. Here are the testing requirements:

To run the tests, use the following command: `python -m unittest discover`

## 6. Contributing
Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (git checkout -b feature-branch).
3. Make your changes.
4. Commit your changes (git commit -am 'Add new feature').
5. Push to the branch (git push origin feature-branch).
6. Create a new Pull Request.

## 7. License
This project is licensed under the MIT License. See the LICENSE file for details.

## 8. Contact
For any questions or suggestions, please open an issue or contact the repository owner.
