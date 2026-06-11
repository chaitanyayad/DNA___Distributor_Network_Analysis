

import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

# India bounding box
LAT_MIN, LAT_MAX = 6.0,  37.6
LON_MIN, LON_MAX = 68.0, 97.5

# 5 km ≈ 0.045 degrees
STEP = 0.045

# City density anchors — (lat, lon, peak_vehicle_count)
# Higher vehicle counts near major cities, tapering off with distance
CITY_ANCHORS = [
    (19.076,  72.877, 9500),   # Mumbai
    (28.613,  77.209, 9500),   # Delhi
    (12.971,  77.594, 8000),   # Bengaluru
    (13.082,  80.270, 7000),   # Chennai
    (17.385,  78.486, 7000),   # Hyderabad
    (22.572,  88.363, 7000),   # Kolkata
    (18.520,  73.856, 5500),   # Pune
    (23.022,  72.571, 5500),   # Ahmedabad
    (21.170,  72.831, 4000),   # Surat
    (26.912,  75.787, 4000),   # Jaipur
    (26.846,  80.946, 4000),   # Lucknow
    (21.145,  79.088, 3000),   # Nagpur
    (22.719,  75.857, 3000),   # Indore
    (23.259,  77.412, 3000),   # Bhopal
    (25.594,  85.137, 3000),   # Patna
    (11.017,  76.966, 2500),   # Coimbatore
    ( 9.931,  76.267, 2500),   # Kochi
    (30.733,  76.779, 2500),   # Chandigarh
    (26.144,  91.736, 2000),   # Guwahati
    (20.296,  85.824, 2000),   # Bhubaneswar
    (17.686,  83.218, 3000),   # Visakhapatnam
    (22.307,  73.181, 3000),   # Vadodara
    (31.634,  74.872, 2000),   # Amritsar
    (25.317,  82.973, 2000),   # Varanasi
    (12.914,  74.856, 2000),   # Mangaluru
]


def vehicle_count_at(lat, lon):
    """
    Compute vehicle count for a grid cell using Gaussian falloff from each
    city anchor. Cells near multiple cities get additive contribution.
    """
    total = 50.0  # baseline rural count
    for (c_lat, c_lon, peak) in CITY_ANCHORS:
        dist_deg = np.sqrt((lat - c_lat)**2 + (lon - c_lon)**2)
        dist_km  = dist_deg * 111.0
        # Gaussian with sigma=80 km — gradual falloff across metro region
        contribution = peak * np.exp(-0.5 * (dist_km / 80.0)**2)
        total += contribution
    return total


# ─────────────────────────────────────────────────────────────────────────────
# BUILD GRID
# ─────────────────────────────────────────────────────────────────────────────
lats = np.arange(LAT_MIN, LAT_MAX, STEP)
lons = np.arange(LON_MIN, LON_MAX, STEP)

print(f"Grid dimensions: {len(lats)} lat × {len(lons)} lon = {len(lats)*len(lons):,} cells")

rows = []
grid_id = 1

for lat in lats:
    for lon in lons:
        base_count = vehicle_count_at(lat, lon)

        # 12% Gaussian noise to simulate real-world variance
        noise_factor = np.random.normal(1.0, 0.12)
        vehicle_count = max(1, round(base_count * noise_factor))

        # Average vehicle age — older in rural/smaller cities
        # Range 3–12 years, skewed older away from metro areas
        avg_age = round(np.random.uniform(3.5, 10.0), 1)

        # Commercial vehicle % — higher in logistics corridors
        # Range 5–45%, baseline 15% with regional variation
        commercial_pct = round(min(0.45, max(0.05,
            np.random.normal(0.15, 0.08)
        )), 3)

        rows.append({
            "grid_id":          f"GRID-{grid_id:07d}",
            "center_lat":       round(lat + STEP / 2, 6),
            "center_lon":       round(lon + STEP / 2, 6),
            "vehicle_count":    vehicle_count,
            "avg_vehicle_age":  avg_age,
            "commercial_pct":   commercial_pct,
            # Derived feature used by ML model
            "weighted_score":   round(
                vehicle_count * commercial_pct / max(avg_age, 0.1), 4
            ),
        })
        grid_id += 1

df = pd.DataFrame(rows)

out_path = Path(__file__).parent.parent / "data" / "raw" / "vehicle_grid.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(out_path, index=False)

print(f"Generated {len(df):,} grid cells → {out_path}")
print(f"Vehicle count stats:\n{df['vehicle_count'].describe().round(0)}")