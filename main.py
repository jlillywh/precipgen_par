import tkinter as tk
from tkinter import filedialog
from pgpar import PrecipGenPAR

def main():

    # Title of the program
    title = "Parameter Generator for the Precipitation Simulator"
    version = "version 1.0"

    # Set a fixed width for the border
    width = 60

    # Create a border made of '*' symbols
    border = '*' * width

    # Print the bordered title and version
    print(border)
    print(f"* {title:<{width-4}} *")  # Use string formatting to pad the title with spaces
    print(f"* {version:<{width-4}} *")  # Use string formatting to pad the version with spaces
    print(border)

    # Welcome message
    print("Welcome to the Precipitation Generator using the PAR model!")
    # Create a new PGPar object
    pgpar1 = PrecipGenPAR()

    while True:
        print("\nPlease choose from the following commands:")
        print("L: Load Time Series")
        print("K: Peek at Time Series")
        print("T: Plot Time Series")
        print("G: Generate Parameters")
        print("M: Show Parameters")
        print("S: Save Parameters")
        print("X: Exit")

        command = input("Enter command: ").upper()

        if command == 'L':
            # Load the data
            # Open a file dialog to request file name from user
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            file_path = filedialog.askopenfilename()

            # Load the data
            pgpar1.parse_ts_csv(file_path)
        elif command == 'P':
            # Peek at the time series
            pgpar1.print_head()
        elif command == 'T':
            # Plot the time series
            pgpar1.plot_ts()
        elif command == 'G':
            # Generate parameters
            pgpar1.gen_params()
        elif command == 'X':
            # Exit the program
            print("Goodbye!")
            break
        else:
            print("Invalid command. Please try again.")


if __name__ == "__main__":
    main()