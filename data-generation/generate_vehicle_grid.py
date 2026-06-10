import pandas as pd
import numpy as np
import os

np.random.seed(42)

LAT_MIN, LAT_MAX = 8.0, 37.0
LON_MIN, LON_MAX = 68.5, 97.5

GRID_SIZE_DEG = 5 / 111.0  # ~5 km per cell

POPULATION_CENTERS = [
    # lat,     lon,    weight
    (19.076,  72.877, 100),   # Mumbai
    (28.613,  77.209, 100),   # Delhi
    (12.971,  77.594,  90),   # Bengaluru
    (13.082,  80.270,  80),   # Chennai
    (17.385,  78.486,  80),   # Hyderabad
    (22.572,  88.363,  80),   # Kolkata
    (18.520,  73.856,  60),   # Pune
    (23.022,  72.571,  60),   # Ahmedabad
    (21.170,  72.831,  50),   # Surat
    (26.912,  75.787,  50),   # Jaipur
    (26.846,  80.946,  45),   # Lucknow
    (21.145,  79.088,  40),   # Nagpur
    (22.719,  75.857,  40),   # Indore
    (23.259,  77.412,  40),   # Bhopal
    (25.594,  85.137,  40),   # Patna
    (11.017,  76.966,  35),   # Coimbatore
    ( 9.931,  76.267,  35),   # Kochi
    (30.733,  76.779,  35),   # Chandigarh
    (26.144,  91.736,  30),   # Guwahati
    (20.296,  85.824,  30),   # Bhubaneswar
    (17.686,  83.218,  38),   # Visakhapatnam
    (22.307,  73.181,  38),   # Vadodara
    (31.634,  74.872,  30),   # Amritsar
    (25.317,  82.973,  30),   # Varanasi
    (12.914,  74.856,  28),   # Mangaluru
]

def compute_vehicle_density(lat, lon):
    density = 5.0  # rural baseline
    for clat, clon, weight in POPULATION_CENTERS:
        dist_km = np.sqrt(
            ((lat - clat) * 111) ** 2 +
            ((lon - clon) * 111 * np.cos(np.radians(lat))) ** 2
        )
        density += weight * np.exp(-(dist_km ** 2) / (2 * 80 ** 2))
    return density

records = []
lat = LAT_MIN
while lat < LAT_MAX:
    lon = LON_MIN
    while lon < LON_MAX:
        density_score = compute_vehicle_density(lat, lon)

        if density_score < 2.0:
            lon += GRID_SIZE_DEG
            continue

        # Base vehicle count from density
        vehicle_count = int(np.random.poisson(lam=density_score * 15))
        if vehicle_count < 5:
            lon += GRID_SIZE_DEG
            continue

        # Add 12% Gaussian noise — simulates real-world variance
        # (highway corridors, flood zones, industrial pockets, etc.)
        noise_factor  = np.random.normal(1.0, 0.12)
        vehicle_count = max(5, int(vehicle_count * noise_factor))

        avg_vehicle_age  = round(float(np.clip(np.random.normal(7.5, 2.0), 1.0, 20.0)), 1)
        commercial_pct   = round(float(np.random.beta(a=2, b=5) * 100), 1)

        records.append({
            "grid_id":                f"G-{len(records)+1:07d}",
            "center_lat":             round(lat + GRID_SIZE_DEG / 2, 5),
            "center_lon":             round(lon + GRID_SIZE_DEG / 2, 5),
            "vehicle_count":          vehicle_count,
            "avg_vehicle_age":        avg_vehicle_age,
            "commercial_pct":         commercial_pct,
            "weighted_vehicle_score": round(
                vehicle_count * (commercial_pct / 100) / max(avg_vehicle_age, 0.5), 2
            ),
        })

        lon += GRID_SIZE_DEG
    lat += GRID_SIZE_DEG

os.makedirs("../data/raw", exist_ok=True)
df = pd.DataFrame(records)
df.to_csv("../data/raw/vehicle_grid.csv", index=False)
print(f"Generated {len(df):,} grid cells → ../data/raw/vehicle_grid.csv")

# Sanity check — vehicle count distribution
print("\nVehicle count distribution (sanity check):")
print(df["vehicle_count"].describe().round(1).to_string())