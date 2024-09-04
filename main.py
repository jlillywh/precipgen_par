from fetch_ghcn import fetch_ghcn_data
from parse_ghcn import parse_ghcn_data
from analyze_precip_ts import get_station_info, summarize_dataset
from pgpar import PrecipGenPAR

def main() -> None:
    station_id = input("Enter the GHCN station ID: ")
    
    print(f"Fetching data for station {station_id}...")
    station_info = get_station_info(station_id)
    raw_data = fetch_ghcn_data(station_id)
    
    if raw_data:
        df = parse_ghcn_data(raw_data)
        
        if df is not None and not df.empty:
            pgp = PrecipGenPAR(df)
            summarize_dataset(df, station_info, pgp)
            
            units = "inches" if df['PRCP'].max() < 100 else "mm"
            print(f"\nPrecipitation units: {units}")
            
            params = pgp.get_parameters()
            
            output_file = f"{station_id}_precipitation_parameters.csv"
            with open(output_file, 'w') as f:
                for condition in ['dry', 'all', 'wet']:
                    f.write(f"{condition.capitalize()} Years Parameters:\n")
                    params[condition].to_csv(f, index=False)
                    f.write("\n")
                    print(f"\n{condition.capitalize()} Years Parameters:")
                    print(params[condition].to_string(index=False))
                    print()
            print(f"\nResults saved to {output_file}")
        else:
            print("No valid data to process.")
    else:
        print("Failed to fetch data. Please check the station ID and try again.")

if __name__ == "__main__":
    main()