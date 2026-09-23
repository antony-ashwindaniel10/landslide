import os
import pandas as pd

input_file = "data/historical/historical_landslides.csv"
output_file = "data/satellite/satellite_input.csv"

# Create satellite folder if it does not exist
os.makedirs("data/satellite", exist_ok=True)

# Load historical data
df = pd.read_csv(input_file)

# Create a satellite-data template
satellite_df = df[
    [
        "latitude",
        "longitude",
        "slope",
        "elevation"
    ]
].copy()

# Placeholder columns for future real satellite data
satellite_df["ndvi"] = 0.0
satellite_df["soil_moisture"] = 0.0
satellite_df["surface_deformation"] = 0.0

# Save the satellite input template
satellite_df.to_csv(output_file, index=False)

print("Satellite data template created successfully.")
print(f"Total locations: {len(satellite_df)}")
print(f"Saved to: {output_file}")
print()
print(satellite_df)