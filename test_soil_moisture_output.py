import pandas as pd

FILE = "data/processed/event_soil_moisture_power.csv"

df = pd.read_csv(FILE)

print("=" * 65)
print("SOIL MOISTURE OUTPUT VERIFICATION")
print("=" * 65)

print(f"Total records : {len(df)}")
print(f"Columns       : {list(df.columns)}")

print("\nMissing values:")
print(df.isnull().sum())

print("\nSoil wetness statistics:")
print(f"Minimum : {df['soil_wetness_gwet_top'].min():.4f}")
print(f"Maximum : {df['soil_wetness_gwet_top'].max():.4f}")
print(f"Mean    : {df['soil_wetness_gwet_top'].mean():.4f}")

print("\nSource distribution:")
print(df["soil_moisture_source"].value_counts())

print("\nFirst 5 records:")
print(df.head())

print("\n" + "=" * 65)
print("VERIFICATION COMPLETE")
print("=" * 65)