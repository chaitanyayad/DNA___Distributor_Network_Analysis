

import pandas as pd
import numpy as np
from faker import Faker
import random
from pathlib import Path

fake = Faker('en_IN')
random.seed(42)
np.random.seed(42)

CITIES = [
    ("Mumbai",        "Maharashtra",    19.076,  72.877,  60, 1, 12),
    ("Delhi",         "Delhi",          28.613,  77.209,  60, 1, 12),
    ("Bengaluru",     "Karnataka",      12.971,  77.594,  60, 1, 10),
    ("Chennai",       "Tamil Nadu",     13.082,  80.270,  60, 1,  8),
    ("Hyderabad",     "Telangana",      17.385,  78.486,  60, 1,  8),
    ("Kolkata",       "West Bengal",    22.572,  88.363,  60, 1,  8),
    ("Pune",          "Maharashtra",    18.520,  73.856,  45, 1,  6),
    ("Ahmedabad",     "Gujarat",        23.022,  72.571,  45, 1,  6),
    ("Surat",         "Gujarat",        21.170,  72.831,  45, 1,  4),
    ("Jaipur",        "Rajasthan",      26.912,  75.787,  45, 1,  4),
    ("Lucknow",       "Uttar Pradesh",  26.846,  80.946,  35, 2,  4),
    ("Nagpur",        "Maharashtra",    21.145,  79.088,  35, 2,  3),
    ("Indore",        "Madhya Pradesh", 22.719,  75.857,  35, 2,  3),
    ("Bhopal",        "Madhya Pradesh", 23.259,  77.412,  35, 2,  3),
    ("Patna",         "Bihar",          25.594,  85.137,  35, 2,  3),
    ("Coimbatore",    "Tamil Nadu",     11.017,  76.966,  25, 3,  2),
    ("Kochi",         "Kerala",          9.931,  76.267,  25, 3,  2),
    ("Chandigarh",    "Punjab",         30.733,  76.779,  25, 3,  2),
    ("Guwahati",      "Assam",          26.144,  91.736,  25, 3,  2),
    ("Bhubaneswar",   "Odisha",         20.296,  85.824,  25, 3,  2),
    ("Visakhapatnam", "Andhra Pradesh", 17.686,  83.218,  30, 2,  3),
    ("Vadodara",      "Gujarat",        22.307,  73.181,  30, 2,  3),
    ("Amritsar",      "Punjab",         31.634,  74.872,  25, 3,  2),
    ("Varanasi",      "Uttar Pradesh",  25.317,  82.973,  25, 3,  2),
    ("Mangaluru",     "Karnataka",      12.914,  74.856,  25, 3,  2),
]

# ─────────────────────────────────────────────────────────────────────────────
# HIGHWAY TOWNS
# Real towns along major national highways where workshops naturally cluster:
# truck stops, industrial areas, market towns, transport hubs.
# Each town will get 15-45 workshops with ±4 km jitter.
# Dealers are city-only, so highway towns far from cities become white spaces.
# ─────────────────────────────────────────────────────────────────────────────
HIGHWAY_TOWNS = [
    # NH44 — Delhi to Kanyakumari
    [(27.9,77.6),(26.7,78.0),(25.5,78.7),(24.2,78.9),(23.2,79.1),
     (21.7,79.0),(20.5,79.3),(18.9,79.4),(17.4,78.5),(16.0,77.7),
     (14.0,77.0),(11.5,77.1),(10.0,77.3)],
    # NH48 — Delhi to Chennai via Jaipur
    [(27.5,76.2),(26.5,75.5),(25.3,74.2),(24.0,73.2),(22.5,72.7),
     (20.9,72.9),(19.9,73.1),(18.5,73.9),(17.0,74.3),(15.5,75.0)],
    # NH19 — Delhi to Kolkata
    [(27.9,78.1),(27.1,79.5),(26.4,81.2),(25.5,82.5),(25.4,83.5),
     (25.6,84.8),(25.5,85.8),(24.5,87.1),(23.5,88.0)],
    # NH27 — East West corridor
    [(23.2,86.0),(23.0,84.5),(22.3,82.5),(21.5,81.2),(21.2,79.5),
     (22.3,77.5),(22.8,75.5)],
    # NH16 — Kolkata to Chennai coastal
    [(21.5,87.0),(20.5,86.5),(19.3,85.0),(18.3,84.0),(17.5,83.0),
     (15.8,80.5),(14.5,80.0)],
    # NH66 — Mumbai to Kanyakumari coastal
    [(18.5,73.1),(17.0,73.5),(15.3,74.1),(13.5,74.6),(11.7,75.5),(9.8,76.3)],
    # NH53 — Habibganj to Kolkata
    [(23.5,78.2),(23.7,80.0),(22.8,82.0),(22.6,85.0)],
    # NH30 — Interior Chhattisgarh
    [(19.5,82.1),(20.3,81.6),(21.0,81.5)],
    # NH37 — Assam corridor
    [(26.3,92.0),(26.6,93.0),(26.9,94.0)],
    # NH52 — Punjab
    [(31.2,75.2),(30.9,76.0),(30.5,77.0)],
    # NH58 — Delhi to Haridwar
    [(29.0,77.5),(29.5,77.9),(29.9,78.1)],
    # NH62 — Rajasthan interior
    [(26.3,74.8),(25.8,73.5),(25.3,72.5)],
]


def generate_town_workshops(town_lat, town_lon, jitter_km=4):
    """
    Place workshops around a highway town.
    Count varies 15-45 per town — organic, not fixed.
    Jitter ±4 km — tight enough to cluster, realistic for a small town.
    """
    count = random.randint(15, 45)
    pts = []
    for _ in range(count):
        jlat = random.uniform(-jitter_km, jitter_km) / 111.0
        jlon = random.uniform(-jitter_km, jitter_km) / 111.0
        pts.append((round(town_lat + jlat, 6), round(town_lon + jlon, 6)))
    return pts


# Pre-generate all highway town coordinates
all_highway_coords = []
for highway in HIGHWAY_TOWNS:
    for (lat, lon) in highway:
        all_highway_coords.extend(generate_town_workshops(lat, lon))

random.shuffle(all_highway_coords)
print(f"Highway town workshops available: {len(all_highway_coords)}")

city_names   = [c[0] for c in CITIES]
city_weights = [c[6] for c in CITIES]
city_lookup  = {c[0]: c for c in CITIES}


def pick_city():
    return random.choices(city_names, weights=city_weights, k=1)[0]


def jittered_coords(city_name, jitter_km=8):
    c = city_lookup[city_name]
    lat_c, lon_c = c[2], c[3]
    jitter_lat = random.uniform(-jitter_km, jitter_km) / 111.0
    jitter_lon = random.uniform(-jitter_km, jitter_km) / (
        111.0 * np.cos(np.radians(lat_c))
    )
    return round(lat_c + jitter_lat, 6), round(lon_c + jitter_lon, 6)


def make_record(entity_type, prefix, index, city_name=None, lat=None, lon=None):
    uid = f"{prefix}-{str(index).zfill(4)}"
    if lat is not None and lon is not None:
        city  = "Rural"
        state = "Unknown"   # corrected by validate_locations.py Layer 3
    else:
        if city_name is None:
            city_name = pick_city()
        city_data = city_lookup[city_name]
        lat, lon  = jittered_coords(city_name)
        city      = city_name
        state     = city_data[1]

    return {
        "id":             uid,
        "name":           f"{fake.company()} {entity_type} ({uid})",
        "type":           entity_type,
        "city":           city,
        "state":          state,
        "address":        fake.address().replace("\n", ", "),
        "pin_code":       fake.postcode(),
        "contact_person": fake.name(),
        "phone":          fake.phone_number(),
        "latitude":       lat,
        "longitude":      lon,
        "active":         random.random() < 0.95,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GENERATE ALL RECORDS
# ─────────────────────────────────────────────────────────────────────────────
records = []

# Mother Warehouses — one per city (25)
for i, city in enumerate([c[0] for c in CITIES], 1):
    records.append(make_record("Mother Warehouse", "MW", i, city_name=city))

# Additional Warehouses (55)
for i in range(1, 56):
    records.append(make_record("Additional Warehouse", "AW", i))

# Retail Offices (180)
for i in range(1, 181):
    records.append(make_record("Retail Office", "RO", i))

# Dealers (700) — ALL city-based, zero on highways
for i in range(1, 701):
    records.append(make_record("Dealer", "DLR", i))

# Independent Workshops (4500)
# 50% city | 35% highway towns | 15% remote scattered
city_count    = 0
highway_count = 0
remote_count  = 0
hw_idx        = 0

for i in range(1, 4501):
    r = random.random()
    if r < 0.50:
        records.append(make_record("Independent Workshop", "IW", i))
        city_count += 1
    elif r < 0.85 and hw_idx < len(all_highway_coords):
        lat, lon = all_highway_coords[hw_idx]
        hw_idx  += 1
        records.append(make_record("Independent Workshop", "IW", i,
                                   lat=lat, lon=lon))
        highway_count += 1
    else:
        # Remote — random scatter across India, mostly DBSCAN noise
        lat = round(random.uniform(8.5, 35.0), 6)
        lon = round(random.uniform(69.5, 95.5), 6)
        records.append(make_record("Independent Workshop", "IW", i,
                                   lat=lat, lon=lon))
        remote_count += 1

print(f"Workshops: {city_count} city | {highway_count} highway | {remote_count} remote")

# MASS (400) — city-based
for i in range(1, 401):
    records.append(make_record("MASS", "MASS", i))

# ─────────────────────────────────────────────────────────────────────────────
# WRITE OUTPUT
# ─────────────────────────────────────────────────────────────────────────────
out_dir = Path(__file__).parent.parent / "data" / "raw"
out_dir.mkdir(parents=True, exist_ok=True)

df = pd.DataFrame(records)
df.to_csv(out_dir / "locations.csv", index=False)
print(f"\nGenerated {len(df)} location records → {out_dir / 'locations.csv'}")

city_ref = pd.DataFrame([{
    "city":              c[0],
    "state":             c[1],
    "center_lat":        c[2],
    "center_lon":        c[3],
    "allowed_radius_km": c[4],
    "tier":              c[5],
} for c in CITIES])
city_ref.to_csv(out_dir / "city_reference.csv", index=False)
print(f"Saved city reference → {out_dir / 'city_reference.csv'}")