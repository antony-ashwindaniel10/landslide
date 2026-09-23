from backend.dem_service import get_terrain_features


latitude = 27.4728
longitude = 94.912


features = get_terrain_features(
    latitude,
    longitude
)


print("Latitude:", latitude)
print("Longitude:", longitude)
print("Elevation:", features["elevation_m"], "meters")
print("Slope:", features["slope_degrees"], "degrees")

