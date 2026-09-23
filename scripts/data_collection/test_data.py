import json

sample_data = {
    "latitude": 27.4728,
    "longitude": 94.9120,
    "rainfall": 120,
    "soil_moisture": 65,
    "slope": 35,
    "elevation": 1200,
    "historical_landslide": True
}

print(json.dumps(sample_data, indent=4))