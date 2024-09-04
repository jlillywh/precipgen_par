import os
import logging
import requests
from io import StringIO
import pandas as pd
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog, scrolledtext
import tkinter.messagebox as messagebox
import json
from pgpar import PrecipGenPAR
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Entry point for the program.
# Define the App class, which is the user interface for the PrecipGen PAR application
# Goal is to simplify the process of calculating the 12x4 input table used by 
# PrecipGen to generate synthetic daily precipitation data. Using a csv file containing
# daily precipitation data, the app will calculate the parameters for each month and
# display them to the user with ability to export to csv. The user can also save the configuration to a json file.
class App:
    # Initialize the main app window
    # Populate input controls with default values
    def __init__(self, root):
        # Entire window
        self.root = root
        self.root.title("PrecipGen PAR")
        self.root.minsize(800, 500)

        # Everything below the menu bar goes in the main frame
        self.main = tk.Frame(self.root)
        margin = 0.05
        self.main.place(relx=margin,rely=margin, relwidth=1-2*margin, relheight=1-2*margin)
        
        # Business logic
        self.config = self.default_config()
        self.last_saved_config = self.config.copy()
        self.config_file_path = None  # Track the path where the config was last saved

        self.time_series_path = ''  # Initialize with an empty string

        self.time_series_definition = pd.DataFrame()
        self.params = pd.DataFrame()
        self.autocorrelation = 0.0
        self.optimal_lag = 0
        
        # Create the widgets
        self.units_selector = tk.StringVar(self.main, value=self.config['units'])
        self.time_series_file_name_display = tk.StringVar(self.main, value='')
        self.time_series_display = scrolledtext.ScrolledText(self.main)
        self.initialize_widget_frames()

        # Handle responses to user input
        self.time_series_file_name_display.trace_add('write', self.update_time_series_file_path)
        self.units_selector.trace_add('write', self.update_units)

        # Create the menu bar (ensure created after the widgets)
        self.create_menu()
    
    def create_menu(self):
        # Create a menu bar
        menubar = tk.Menu(self.root)

        # Create a File menu and add it to the menu bar
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.reset_app)
        filemenu.add_command(label="Open", command=self.open)
        filemenu.add_command(label="Save", command=self.save)
        filemenu.add_command(label="Save As", command=self.save_as)

        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.exit)
        menubar.add_cascade(label="File", menu=filemenu)

        # Create a Data menu and add it to the menu bar
        datamenu = tk.Menu(menubar, tearoff=0)
        datamenu.add_command(label="Import from CSV", command=self.import_csv)  # Ensure you have a method self.import_csv
        datamenu.add_command(label="Download from GHCN database", command=self.download_ghcn)
        menubar.add_cascade(label="Data", menu=datamenu)

        # Create a Model menu and add it to the menu bar
        modelmenu = tk.Menu(menubar, tearoff=0)
        modelmenu.add_command(label="View Configuration", command=self.view_config)
        modelmenu.add_command(label="Format Time Series", command=self.format_time_series)
        modelmenu.add_command(label="Load Time Series", command=self.browse_file)
        modelmenu.add_command(label="Calculate PrecipGen Parameters", command=self.calculate_params)
        modelmenu.add_command(label="Show Parameters", command=self.create_params_window)
        modelmenu.add_command(label="Export Parameters", command=self.export_parameters)  # Add this line
        menubar.add_cascade(label="Model", menu=modelmenu)

        # Create an About menu and add it to the menu bar
        aboutmenu = tk.Menu(menubar, tearoff=0)
        aboutmenu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="About", menu=aboutmenu)

        # Configure the menu bar at the end of the sequence
        self.root.config(menu=menubar)
    
    def initialize_widget_frames(self):
        self.create_title_frame()
        self.create_units_frame()
        self.create_ts_file_frame()
        self.create_file_preview_frame()
    
    def create_title_frame(self):
        title_frame = tk.Frame(self.main)
        title_frame.pack(side="top", pady=10)

        title = tk.Label(
            title_frame, 
            text="Parameter Generator for PrecipGen", 
            font=("Helvetica", 12),
            anchor='w')
        title.pack(fill=tk.X, pady=10)
    
    # Goal of this region is to help user verify the file they selected
    def create_ts_file_frame(self):
        file_frame = tk.Frame(self.main)
        file_frame.pack(side="top", pady=10)

        # Create the label "Time Series of Daily Precipitation:"
        self.ts_label = tk.Label(file_frame, text="Input Time Series File:")
        self.ts_label.pack(side="left")

        # Create a StringVar linked to the Entry widget
        self.file_name_var = tk.StringVar()
        #self.file_name_var.set(self.time_series_label.get())

        # Extract the file name from the path and set it to the StringVar
        file_name = self.get_time_series_file_name(self.time_series_path)
        self.file_name_var.set(file_name)

        # Create the Entry "File name: {self.time_series_file_name}"
        self.file_name_label = tk.Entry(file_frame, textvariable=self.file_name_var, state='readonly', readonlybackground='light gray', width=60)
        self.file_name_label.pack(side="left")
    
    # This region shows the user the units of the precipitation data
    def create_units_frame(self):
        units_frame = tk.Frame(self.main)
        units_frame.pack(side="top", pady=10)

        # Create a label for the units dropdown
        units_label = tk.Label(units_frame, text="Precipitation Units:")
        units_label.pack(side=tk.LEFT)

        # Create a variable to store the selected value
        self.units_selector = tk.StringVar(units_frame)
        self.units_selector.set(self.config['units'])

        # Create a dropdown menu for the units
        units_dropdown = tk.OptionMenu(units_frame, self.units_selector, 'in', 'mm')
        units_dropdown.pack(side=tk.LEFT)
    
    # This region shows a preview of the time series data for visual verification
    def create_file_preview_frame(self):
        self.file_preview_frame = tk.Frame(self.main)
        self.file_preview_frame.pack(side="top", pady=10, fill=tk.BOTH, expand=True)

        time_series_label = tk.Label(self.file_preview_frame, text="Annual Total Precipitation:")
        time_series_label.pack()

        # Initially, display a message
        self.initial_message = tk.Label(self.file_preview_frame, text="No file loaded. Please select a time series file.")
        self.initial_message.pack(fill=tk.BOTH, expand=True)

    def format_time_series(self, date_col_index, precip_col_index):
        try:
            # Load the file with pandas
            df = pd.read_csv(self.time_series_path)

            # Check if the specified column indices are valid
            if date_col_index >= len(df.columns) or precip_col_index >= len(df.columns):
                messagebox.showerror("Error", "Invalid column index. Please check your input.")
                return

            # Create a new DataFrame with only the specified columns
            formatted_df = pd.DataFrame({
                'DATE': df.iloc[:, date_col_index],
                'PRCP': df.iloc[:, precip_col_index]
            })

            # Convert 'DATE' to datetime
            formatted_df['DATE'] = pd.to_datetime(formatted_df['DATE'])

            # Update the time series definition
            self.time_series_definition = formatted_df

            # Update the config with the new file path
            self.config['ts_file_path'] = self.time_series_path
            self.file_name_var.set(os.path.basename(self.time_series_path))
            
            # Load the formatted time series
            self.load_time_series()

        except ValueError:
            messagebox.showerror("Error", "Please enter valid integer indices for the columns.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to format file: {e}")

    def process_file(self, date_col_index, precip_col_index):
        # Assuming the user has already selected a file to format
        file_path = filedialog.askopenfilename()  # Let the user select the file
        if not file_path:
            messagebox.showerror("Error", "No file selected.")
            return

        try:
            # Convert indices from string to integer, use defaults if empty
            date_col_index = int(date_col_index) if date_col_index else 0
            precip_col_index = int(precip_col_index) if precip_col_index else 1

            # Load the file with pandas
            df = pd.read_csv(file_path)

            # Check if the specified column indices are valid
            if date_col_index >= len(df.columns) or precip_col_index >= len(df.columns):
                messagebox.showerror("Error", "Invalid column index. Please check your input.")
                return

            # Keep only the specified columns and rename them
            formatted_df = df.iloc[:, [date_col_index, precip_col_index]]
            formatted_df.columns = ['DATE', 'PRCP']

            # Save the formatted DataFrame
            save_path = filedialog.asksaveasfilename(defaultextension=".csv")
            if save_path:
                formatted_df.to_csv(save_path, index=False)
                messagebox.showinfo("Success", "File formatted and saved successfully.")
                
                # Update the config with the new file path
                self.config['ts_file_path'] = save_path
                self.time_series_path = save_path
                self.file_name_var.set(os.path.basename(save_path))
                
                # Load the formatted time series
                self.load_time_series()
            else:
                messagebox.showerror("Error", "Save operation cancelled.")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid integer indices for the columns.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to format file: {e}")

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.time_series_path = file_path
            self.update_config('ts_file_path', file_path)
            file_name = os.path.basename(file_path)
            self.time_series_file_name_display.set(file_name)
            self.file_name_var.set(file_name)
            self.load_time_series()  # Call this after setting the path
        
    def check_missing_data(self, df):
        # Calculate the date range
        start_date = df['DATE'].min()
        end_date = df['DATE'].max()
        
        # Create a complete date range
        complete_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Calculate the number of missing days
        missing_days = len(complete_range) - len(df)
        
        # Calculate the percentage of missing data
        missing_percentage = (missing_days / len(complete_range)) * 100
        
        return missing_percentage
    
    def create_annual_precip_plot(self):
        if self.time_series_definition.empty:
            return

        # Calculate annual total precipitation
        annual_precip = self.time_series_definition.groupby(self.time_series_definition['DATE'].dt.year)['PRCP'].sum().reset_index()
        annual_precip.columns = ['Year', 'Annual Precipitation']

        # Create the plot
        self.create_time_history_plot(
            frame=self.file_preview_frame,
            data=annual_precip,
            x_column='Year',
            y_column='Annual Precipitation',
            title='Annual Total Precipitation',
            xlabel='Year',
            ylabel='Precipitation (mm)'
        )

    def load_time_series(self):
        if not self.time_series_path:
            messagebox.showerror("Error", "No file path specified.")
            return

        try:
            df = pd.read_csv(self.time_series_path)
            
            # Check if 'DATE' and 'PRCP' columns exist
            if 'DATE' not in df.columns or 'PRCP' not in df.columns:
                if 'Date' in df.columns and 'PRCP' in df.columns:
                    df = df.rename(columns={'Date': 'DATE'})
                else:
                    messagebox.showerror("Invalid file", "The file does not have the correct format. Expected 'DATE' (or 'Date') and 'PRCP' columns.")
                    return

            # Convert 'DATE' to datetime and sort
            df['DATE'] = pd.to_datetime(df['DATE'])
            df = df.sort_values('DATE')

            # Keep only 'DATE' and 'PRCP' columns
            df = df[['DATE', 'PRCP']]

            # Print debug information
            print(f"Total records: {len(df)}")
            print(f"Date range: {df['DATE'].min()} to {df['DATE'].max()}")
            print(f"Unique years: {df['DATE'].dt.year.nunique()}")

            # Identify years with data
            year_counts = df.groupby(df['DATE'].dt.year).size()
            print("Year counts:")
            print(year_counts)

            # Instead of filtering for complete years, we'll use all available data
            self.time_series_definition = df

            # Update the plot
            self.create_annual_precip_plot()

            # Inform user about data completeness
            incomplete_years = year_counts[year_counts < 365].index
            if len(incomplete_years) > 0:
                messagebox.showwarning("Incomplete Years", 
                                    f"The following years have incomplete data: {', '.join(map(str, sorted(incomplete_years)))}")

            # Check for missing data
            missing_data_percentage = self.check_missing_data(df)
            if missing_data_percentage > 0:
                messagebox.showwarning("Missing Data", 
                                    f"Warning: Approximately {missing_data_percentage:.2f}% of daily records are missing from the dataset.")

            # If we've made it this far, we have some data to work with
            messagebox.showinfo("Data Loaded", "Time series data has been loaded successfully.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read the file: {str(e)}")
            print(f"Error details: {str(e)}")
            print(f"File path: {self.time_series_path}")
            
    def import_csv(self):
        # Use the existing browse_file method to let the user select a CSV file
        self.browse_file()
        
        if self.time_series_path:
            try:
                # Read the CSV file
                df = pd.read_csv(self.time_series_path)
                
                # Get the column indices for Date and PRCP
                date_col = df.columns.get_loc('Date') if 'Date' in df.columns else df.columns.get_loc('DATE')
                precip_col = df.columns.get_loc('PRCP')
                
                # Use the format_time_series method to process the file
                self.format_time_series(date_col, precip_col)
                
                self.log("INFO", "CSV file imported and formatted successfully.")
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import CSV: {str(e)}")
        else:
            messagebox.showinfo("Import Cancelled", "No file was selected.")
    
    @staticmethod
    def get_ghcn_data(station_id):
        # URL for the data file
        url = f"https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/{station_id}.dly"
        
        # Download the data
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to download data for station {station_id}")
        
        # Read the data into a DataFrame
        data = StringIO(response.text)
        df = pd.read_fwf(data, widths=[11, 4, 2, 4] + [5, 1, 1, 1]*31,
                        names=['ID', 'YEAR', 'MONTH', 'ELEMENT'] +
                            [f'VALUE{i}' for i in range(1, 32)] +
                            [f'MFLAG{i}' for i in range(1, 32)] +
                            [f'QFLAG{i}' for i in range(1, 32)] +
                            [f'SFLAG{i}' for i in range(1, 32)])
        
        # Filter for precipitation data
        df = df[df['ELEMENT'] == 'PRCP']
        
        # Create a list to store the data
        data_list = []
        
        # Process each row
        for _, row in df.iterrows():
            year = int(row['YEAR'])
            month = int(row['MONTH'])
            
            # Determine the number of days in the month
            days_in_month = pd.Timestamp(year, month, 1).days_in_month
            
            for day in range(1, days_in_month + 1):
                value = row[f'VALUE{day}']
                try:
                    value = int(value)
                    if value != -9999:  # -9999 indicates missing data
                        date = pd.Timestamp(year, month, day)
                        prcp = value / 10  # Convert to mm
                        data_list.append({'DATE': date, 'PRCP': prcp})
                except ValueError:
                    # Skip if the value can't be converted to int
                    continue
        
        # Create a new DataFrame from the processed data
        df = pd.DataFrame(data_list)
        
        # Sort by date and reset index
        df = df.sort_values('DATE').reset_index(drop=True)
        
        return df

    def download_ghcn(self):
        # Create a dialog to get the station ID
        station_id = simpledialog.askstring("Station ID", "Enter the GHCN station ID:")
        
        if station_id:
            try:
                # Show a loading message
                loading_window = tk.Toplevel(self.root)
                loading_window.title("Loading")
                loading_label = tk.Label(loading_window, text="Downloading data... Please wait.")
                loading_label.pack(padx=20, pady=20)
                self.root.update()

                # Get the data using the static method
                df = self.get_ghcn_data(station_id)

                # Close the loading window
                loading_window.destroy()

                # Create a file name for the downloaded data
                file_name = f"GHCN_{station_id}.csv"
                
                # Determine the directory to save the file
                if self.config_file_path:
                    save_dir = os.path.dirname(self.config_file_path)
                else:
                    # Use a default directory if no config file path is set
                    save_dir = os.path.join(os.path.expanduser("~"), "PrecipGenPAR_Data")
                    os.makedirs(save_dir, exist_ok=True)
                
                file_path = os.path.join(save_dir, file_name)

                # Save the data to a CSV file
                df.to_csv(file_path, index=False)

                # Update the config with the new file path
                self.config['ts_file_path'] = file_path
                self.time_series_path = file_path
                self.file_name_var.set(file_name)

                # Update the time series definition
                self.time_series_definition = df
                
                # Load the formatted time series
                self.load_time_series()

                # Save the updated configuration
                if self.config_file_path:
                    self.save_config(self.config_file_path)
                else:
                    # If no config file path is set, prompt the user to save the configuration
                    self.save_as()

                messagebox.showinfo("Download Complete", f"Data for station {station_id} has been successfully downloaded, saved to {file_path}, and loaded.")
            except Exception as e:
                messagebox.showerror("Download Error", f"Failed to download data: {str(e)}")
        else:
            messagebox.showinfo("Download Cancelled", "No station ID was entered.")

    def check_missing_data(self, df):
        # Sort the dataframe by date
        df = df.sort_values('DATE')

        # Calculate the date range
        start_date = df['DATE'].min()
        end_date = df['DATE'].max()
        
        # Create a complete date range
        complete_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Calculate the number of missing days
        missing_days = len(complete_range) - len(df)
        
        # Calculate the percentage of missing data
        missing_percentage = (missing_days / len(complete_range)) * 100
        
        return missing_percentage

    def update_time_series_file_path(self, *args):
        # Check if the file exists
        if os.path.isfile(self.time_series_path):
            # Read the CSV file into a dataframe
            self.time_series_definition = pd.read_csv(self.time_series_path)
            # Update ts_head with the new dataframe
            self.time_series_head = self.time_series_definition.head()
            # Update the dataframe display
            self.update_time_series_display()

    def update_time_series_display(self):
        # Clear the text widget
        self.time_series_display.delete('1.0', tk.END)
        
        if not self.time_series_definition.empty:
            # Get the first few rows of the dataframe
            preview_df = self.time_series_definition.head()
            
            # Convert the dataframe to a string representation without the index
            preview_string = preview_df.to_string(index=False)
            
            # Display the preview in the text widget
            self.time_series_display.insert(tk.END, preview_string)
        else:
            self.time_series_display.insert(tk.END, "No file loaded. Please select a time series file.")

    def update_units(self, name, index, mode):
        new_value = self.units_selector.get()
        self.update_config('units', new_value)

    def get_time_series_file_name(self, path):
        return os.path.basename(path)

    def create_time_history_plot(self, frame, data, x_column, y_column, title, xlabel, ylabel):
        # Clear the frame
        for widget in frame.winfo_children():
            widget.destroy()

        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(8, 4))

        # Plot the data
        ax.plot(data[x_column], data[y_column])

        # Set labels and title
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)

        # Adjust layout
        plt.tight_layout()

        # Create a canvas
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)

        # Draw the plot
        canvas.draw()

    def create_annual_precip_plot(self):
        if self.time_series_definition.empty:
            return

        # Calculate annual total precipitation
        annual_precip = self.time_series_definition.groupby(self.time_series_definition['DATE'].dt.year)['PRCP'].sum().reset_index()
        annual_precip.columns = ['Year', 'Annual Precipitation']

        # Create the plot
        self.create_time_history_plot(
            frame=self.file_preview_frame,
            data=annual_precip,
            x_column='Year',
            y_column='Annual Precipitation',
            title='Annual Total Precipitation',
            xlabel='Year',
            ylabel='Precipitation (mm)'
        )

    def view_config(self):
        # Create a new Tkinter Toplevel window
        config_window = tk.Toplevel(self.root)
        config_window.title("Configuration")
        
        # Set the window size (width x height)
        config_window.geometry("400x200")  # Width of 400 pixels should be sufficient for most paths
        
        # Make the window resizable
        config_window.resizable(True, True)
        
        # Create a text widget to display the json content
        config_text = tk.Text(config_window, wrap=tk.WORD)  # Enable word wrapping
        config_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Create vertical scrollbar
        y_scrollbar = tk.Scrollbar(config_text, orient=tk.VERTICAL, command=config_text.yview)
        
        # Configure the text widget to use the scrollbar
        config_text.configure(yscrollcommand=y_scrollbar.set)
        
        # Pack the scrollbar
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insert the json content into the text widget
        formatted_json = json.dumps(self.config, indent=4)
        config_text.insert(tk.END, formatted_json)
        
        # Disable editing in the text widget
        config_text.config(state=tk.DISABLED)

    def export_parameters(self):
        if self.all_params.empty or self.dry_params.empty or self.wet_params.empty:
            messagebox.showwarning("No Parameters", "Please calculate parameters first.")
            return

        # Get the default filename based on the configuration file
        default_filename = "params.csv"
        if self.config_file_path:
            default_filename = os.path.splitext(os.path.basename(self.config_file_path))[0] + "_parameters.csv"

        # Open a file dialog to get the save location and filename
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=default_filename,
            title="Export Parameters"
        )

        if file_path:
            try:
                # Create a list to hold all DataFrames
                dfs = []

                # Add each parameter set with a label
                for label, params in [("All Years", self.all_params), 
                                    ("Dry Years", self.dry_params), 
                                    ("Wet Years", self.wet_params)]:
                    # Add label
                    label_df = pd.DataFrame([[label]], columns=["Parameter Set"])
                    dfs.append(label_df)

                    # Add parameters
                    params_copy = params.copy()
                    params_copy.insert(0, "Parameter Set", label)
                    dfs.append(params_copy)

                    # Add empty row for separation
                    dfs.append(pd.DataFrame([[""]]))

                # Concatenate all DataFrames
                combined_df = pd.concat(dfs, ignore_index=True)

                # Export the combined DataFrame to CSV
                combined_df.to_csv(file_path, index=False)
                messagebox.showinfo("Export Successful", f"Parameters exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export parameters: {str(e)}")

    def create_params_window(self):
        # Create a new window
        params_window = tk.Toplevel()
        params_window.title("PrecipGen Input Parameters")
        params_window.geometry("600x400")  # Set a larger initial size

        # Create a notebook (tabbed interface)
        notebook = ttk.Notebook(params_window)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Function to create a tab for a parameter set
        def create_param_tab(parent, title, params):
            tab = ttk.Frame(parent)
            parent.add(tab, text=title)

            # Create a text widget to display the parameters
            params_display = scrolledtext.ScrolledText(tab)
            params_display.pack(fill=tk.BOTH, expand=True)
            
            # Convert the parameters to a string, including the Month column
            params_string = params.to_string(index=False)
            
            # Insert the parameters string into the text widget
            params_display.insert(tk.END, params_string)

        # Create tabs for each parameter set
        create_param_tab(notebook, "All Years", self.all_params)
        create_param_tab(notebook, "Dry Years", self.dry_params)
        create_param_tab(notebook, "Wet Years", self.wet_params)

        # Create a tab for correlations
        corr_tab = ttk.Frame(notebook)
        notebook.add(corr_tab, text="Correlations")

        # Create a text widget to display the correlations
        corr_display = scrolledtext.ScrolledText(corr_tab)
        corr_display.pack(fill=tk.BOTH, expand=True)

        # Format and insert the correlation information
        corr_string = f"Average PWW-PWD Correlation: {self.pww_pwd_corr:.4f}\n"
        corr_string += f"Average PWW-Mean Correlation: {self.pww_mean_corr:.4f}\n"
        corr_string += f"Autocorrelation of Annual Precip: {self.autocorrelation:.4f}\n"
        corr_string += f"Optimal Lag for Autocorrelation: {self.optimal_lag} year(s)"
        corr_display.insert(tk.END, corr_string)

        # Add a close button
        close_button = ttk.Button(params_window, text="Close", command=params_window.destroy)
        close_button.pack(pady=10)

    def reset_app(self):
        # Reset the app to its initial state
        self.config = self.default_config()
        self.units_selector.set(self.config['units'])
        self.time_series_path = self.config['ts_file_path']
        self.time_series_file_name_display = tk.StringVar(self.main, value=os.path.basename(self.config['ts_file_path']))
        self.time_series_definition = pd.DataFrame()

        # Clear the file name and time series preview display
        self.file_name_var.set('')
        self.time_series_display.delete('1.0', tk.END)
        self.config_file_path = None  # Clear the stored config file path

    def open(self):
        file_path = filedialog.askopenfilename(filetypes=[("Config Files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.config = json.load(f)
                self.config_file_path = file_path
                # Load the configuration from the selected file
                with open(file_path, 'r') as f:
                    self.config = json.load(f)

                self.last_saved_config = self.config.copy()

                # Update the time series file path and units dropdown
                self.time_series_path = self.config['ts_file_path']
                self.units_selector.set(self.config['units'])

                
                self.time_series_file_name_display = tk.StringVar(self.main, value=os.path.basename(self.config['ts_file_path']))
                self.file_name_var.set(self.time_series_file_name_display.get())
                self.time_series_definition = pd.DataFrame()

                # Update the time series display
                self.load_time_series()
                self.update_time_series_file_path(None, None, None)
                self.update_time_series_display()

                self.update_title_bar()  # Add this line
                #messagebox.showinfo("Open Successful", f"Configuration loaded from {file_path}")
            except Exception as e:
                messagebox.showerror("Open Error", f"Failed to open configuration: {str(e)}")

    def save(self):
        if self.config_file_path is None:
            # This is a new file, so we need to use "Save As"
            self.save_as()
        else:
            # We have a file path, so we can just save
            self.save_config(self.config_file_path)

    def save_as(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Save Configuration As"
        )
        if file_path:  # Check if a file path was selected (user didn't cancel)
            return self.save_config(file_path)
        return False  # User cancelled the save_as operation
   
    def save_config(self, file_path):
        try:
            with open(file_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.last_saved_config = self.config.copy()  # Store the last saved state
            self.config_file_path = file_path  # Update the stored file path
            messagebox.showinfo("Save Successful", f"Configuration saved to {file_path}")
            return True
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save configuration: {str(e)}")
            return False

    def custom_save_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Save")
        dialog.geometry("300x100")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make the dialog modal

        label = tk.Label(dialog, text="How would you like to save?")
        label.pack(pady=10)

        result = tk.StringVar()

        def on_button_click(value):
            result.set(value)
            dialog.destroy()

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=5)

        save_button = tk.Button(button_frame, text="Save", command=lambda: on_button_click("Save"))
        save_button.pack(side=tk.LEFT, padx=5)

        save_as_button = tk.Button(button_frame, text="Save As", command=lambda: on_button_click("Save As"))
        save_as_button.pack(side=tk.LEFT, padx=5)

        cancel_button = tk.Button(button_frame, text="Cancel", command=lambda: on_button_click("Cancel"))
        cancel_button.pack(side=tk.LEFT, padx=5)

        self.root.wait_window(dialog)
        return result.get()

    def update_config(self, key, value):
        self.config[key] = value
        # You might want to log this change
        self.log('INFO', f"Configuration updated: {key} = {value}")
        
    def exit(self):
        if self.check_for_changes():
            response = messagebox.askyesnocancel("Unsaved Changes", "There are unsaved changes. Would you like to save before exiting?")
            if response is None:  # User clicked Cancel
                return
            elif response:  # User clicked Yes
                save_response = self.custom_save_dialog()
                
                if save_response == "Cancel":  # User clicked Cancel
                    return
                elif save_response == "Save":  # User clicked Save
                    if not self.save():
                        return  # If save was unsuccessful, don't exit
                elif save_response == "Save As":  # User clicked Save As
                    if not self.save_as():
                        return  # If save_as was cancelled, don't exit
        
        self.root.quit()

    def check_for_changes(self):
        # Compare current state with last saved state
        if hasattr(self, 'last_saved_config'):
            return self.config != self.last_saved_config
        else:
            # If there's no last_saved_config, assume there are changes
            return True
        
    def save(self):
        if self.config_file_path is None:
            # This is a new file, so we need to use "Save As"
            self.save_as()
        else:
            # We have a file path, so we can just save
            self.save_config(self.config_file_path)
        
        # After saving, update the last_saved_config
        self.last_saved_config = self.config.copy()

    def calculate_params(self):
        # Instantiate a new pgpar object
        self.pgpar = PrecipGenPAR(self.time_series_definition.copy())

        # Get all parameter sets (dry, wet, and all) using the new get_parameters method
        all_param_sets = self.pgpar.get_parameters()

        # Store each parameter set separately
        self.dry_params = all_param_sets['dry']
        self.wet_params = all_param_sets['wet']
        self.all_params = all_param_sets['all']

        # Calculate correlations
        self.pww_pwd_corr = self.pgpar.calculate_pww_pwd_correlation()
        self.pww_mean_corr = self.pgpar.calculate_pww_mean_correlation()

        # Calculate the autocorrelation and optimal lag
        self.autocorrelation, self.optimal_lag = self.pgpar.calculate_autocorrelation_ann_precip()

        # If you still need self.params for backwards compatibility, you can set it to all_params
        self.params = self.all_params
        
        # Show message indicating the calculation completed successfully
        messagebox.showinfo("Calculation Complete", "Parameters and correlations have been calculated successfully!")
   
    def show_about(self):
        print("Show about")
   
    def default_config(self):
        return {
            'units': 'mm',
            'ts_file_path': '',
            'date_col': 'DATE',
            'precip_col': 'PRCP'
        }

    def update_title_bar(self):
        base_title = "PrecipGen PAR"
        if self.config_file_path:
            file_name = os.path.basename(self.config_file_path)
            name_without_extension = os.path.splitext(file_name)[0]
            self.root.title(f"{base_title} - {name_without_extension}")
        else:
            self.root.title(base_title)

    def setup_logging(self):
        if not hasattr(self, 'logger'):
            # Determine the log file name
            log_file_name = os.path.splitext(self.config_file_path)[0] + '.log' if self.config_file_path else 'precipgen_par.log'
            
            # Create a logger
            self.logger = logging.getLogger('PrecipGenPAR')
            self.logger.setLevel(logging.INFO)
            
            # Create file handler which logs even debug messages
            fh = logging.FileHandler(log_file_name)
            fh.setLevel(logging.INFO)
            
            # Create formatter and add it to the handler
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            
            # Add the handler to the logger
            self.logger.addHandler(fh)

    def log(self, level, message):
        if not hasattr(self, 'logger'):
            self.setup_logging()
        
        if level == 'INFO':
            self.logger.info(message)
        elif level == 'WARNING':
            self.logger.warning(message)
        elif level == 'ERROR':
            self.logger.error(message)
        elif level == 'CRITICAL':
            self.logger.critical(message)

root = tk.Tk()

# Create a new App object
app = App(root)

# Start the Tk event loop
root.mainloop()
