import numpy as np
import pandas as pd
from math import sqrt, log

# Class to generate precipitation parameters
class PrecipGenPAR:
    # Initialize the object with units and the csv file path
    # The csv is loaded into a DataFrame
    def __init__(self, csv_file_path, units='mm'):
        # Unit conversion factor
        if units == 'in':
            self.unit_convert = 25.4
        else:
            self.unit_convert = 1

        # Load csv into DataFrame
        self.precipitation_data = pd.read_csv(csv_file_path)
        self.precipitation_data = self.precipitation_data[['DATE', 'PRCP']]
        self.precipitation_data['DATE'] = pd.to_datetime(self.precipitation_data['DATE'])
        self.precipitation_data.set_index('DATE', inplace=True)

        # Convert the precipitation values from inches to millimeters
        self.precipitation_data['PRCP'] *= self.unit_convert

        # Number of years in the dataset
        self.nyr = int(len(self.precipitation_data) // 365.25)

        # Initialize output 'params' DataFrame
        self.params = pd.DataFrame(columns=['PWW', 'PWD', 'Mean', 'SD'])
    # Function to get the parameters
    def get_params(self):
        self.pprain()
        return self.params
    # Function to print the parameters
    def print_params(self):
        print(self.get_params())
    # Function to calculate the parameters pww, pwd, mean, and sd
    # Returns a DataFrame with the parameters for each month
    def pprain(self):
        nd = np.zeros(12)
        pppw = np.zeros(12)
        nwd = np.zeros(12)
        nww = np.zeros(12)
        ndd = np.zeros(12)
        ndw = np.zeros(12)
        nw = np.zeros(12)
        sl = np.zeros(12)
        suml = np.zeros(12)
        sum_ = np.zeros(12)
        sum2 = np.zeros(12)
        pww = np.zeros(12)
        pwd = np.zeros(12)
        alpha = np.zeros(12)
        beta = np.zeros(12)
        sum3 = np.zeros(12)
        mean = np.zeros(12)
        sd = np.zeros(12)

        # Convert the index to a datetime format
        self.precipitation_data.index = pd.to_datetime(self.precipitation_data.index)

        # Initialize previous_precipitation
        previous_precipitation = 0.0

        for year in range(self.nyr):
            for dayofyear in range(365):
                # Access the month directly from the index
                month = self.precipitation_data.index[year * 365 + dayofyear].month - 1
        
                precipitation = self.precipitation_data.iloc[year * 365 + dayofyear]['PRCP']
                if precipitation > 0.00:
                    nw[month] += 1
                nd[month] += 1
                if precipitation > 0:
                    if previous_precipitation > 0:
                        nww[month] += 1
                    else:
                        nwd[month] += 1
                    suml[month] += log(precipitation)
                    sum_[month] += precipitation
                    sum2[month] += precipitation * precipitation
                    sum3[month] += precipitation * precipitation * precipitation
                    sl[month] += log(precipitation)
                else:
                    if previous_precipitation > 0:
                        ndw[month] += 1
                    else:
                        ndd[month] += 1
                previous_precipitation = precipitation

        for m in range(12):
            xxnd = nd[m]
            yynw = nw[m]
            pppw[m] = yynw / xxnd

            if nw[m] < 3:
                continue
            xnww = nww[m]
            xnwd = nwd[m]
            xxnw = nww[m] + ndw[m]
            xnd = ndd[m] + nwd[m]
            xnw = nw[m]
            pww[m] = xnww / xxnw
            pwd[m] = xnwd / xnd
            rbar = sum_[m] / xnw
            rlbar = suml[m] / xnw
            y = log(rbar) - rlbar
            anum = 8.898919 + 9.05995 * y + 0.9775373 * y * y
            adom = y * (17.79728 + 11.968477 * y + y * y)
            alpha = min(anum / adom, 0.998)
            beta = rbar / alpha
            lam = 1 / beta
            mean[m] = alpha / lam
            sd[m] = sqrt(alpha) / lam
            self.params.loc[m] = [pww[m], pwd[m], mean[m], sd[m]]
    # Function to export the parameters to a csv file
    def export_params_csv(self, output_file):
        self.params.to_csv(output_file, index=False)