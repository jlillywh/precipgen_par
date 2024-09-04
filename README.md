# PrecipGen Parameter Generator

## 1. Introduction
The `PrecipGenPAR` program produces the input poarameters needed to run a stochastic precipitation simulator called "PrecipGen." PrecipGen is a first-order, 2-state Markov chain-gamma model that simulates daily precipitation for a long-term simulation at a single point on the earth. A Markov process models the change between 2 states (wet vs dry) randomly over time and the probability of a state change depends on the previous state. Precipitation rate is modeled by sampling from a gamma probability distribution. Leveraging the foundational work of Dee Allen Wright and the WGEN model from 1983, implemented in FORTRAN, this program inherits a legacy of reliability in precipitation simulation. This implementation has the added option to incorporate long-term cyclic behavior, based correlations found in the historical record.

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

### 3.2 Run PrecipGenPAR
Once you have the time series, you can run the preprocessor, `PrecipGenPAR`. This requires a configuration file that points to a CSV file containing the daily precipitation data. When you run `PrecipGenPAR`, you need to load the time series. The JSON file should have a reference to the path to this file.

### 3.3 Generate Input Parameters
After initializing a new simulation, use a function in `PrecipGenPAR` to generate the input parameters. These parameters will be used as input to `PrecipGen`.

### 3.4 Execute a Simulation
To execute a simulation, you need the start and end dates, which are defined in the JSON file. The simulation starts on the start date and walks forward in time one day at a time. During each update, `PrecipGen` calculates a new output, which is the rainfall for the day. This continues until the end date is reached.

### 3.5 Results
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

### 4.2 Running the PrecipGenPAR Script

1. **Run the script:**

    ```sh
    python pgpar_cmd.py
    ```

2. **Follow the prompts:**

    - Enter the GHCN station ID when prompted.

3. **View the results:**

    - The script will fetch and process the data, then save the results to a CSV file named `<station_id>_precipitation_parameters.csv`.

### 9.3 Example

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

## 4. Testing
The `PrecipGen` project includes a suite of tests to verify its functionality. Here are the testing requirements:

To run the tests, use the following command: `python -m unittest discover`

## 10. Contributing
Contributions are welcome! Please follow these steps:

Fork the repository.
Create a new branch (git checkout -b feature-branch).
Make your changes.
Commit your changes (git commit -am 'Add new feature').
Push to the branch (git push origin feature-branch).
Create a new Pull Request.
## 11. License
This project is licensed under the MIT License. See the LICENSE file for details.

## 12. Contact
For any questions or suggestions, please open an issue or contact the repository owner.