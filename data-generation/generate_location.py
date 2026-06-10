import pandas as pd
import numpy as np
from faker import Faker
import random
import os

fake = Faker('en_IN')
random.seed(42)
np.random.seed(42)

# ── City reference table ────────────────────────────────────────────────────
# Each city: (lat, lon, allowed_radius_km, tier, weight)
# Weight controls how many pins land here vs other cities
CITIES = [
    # ── Tier 1 Metros (weight 8–12) ─────────────────────────────────────────
    ("Mumbai",        "Maharashtra",    19.076,  72.877,  60, 1, 12),
    ("Delhi",         "Delhi",          28.613,  77.209,  60, 1, 12),
    ("Bengaluru",     "Karnataka",      12.971,  77.594,  60, 1, 10),
    ("Chennai",       "Tamil Nadu",     13.082,  80.270,  60, 1, 8),
    ("Hyderabad",     "Telangana",      17.385,  78.486,  60, 1, 8),
    ("Kolkata",       "West Bengal",    22.572,  88.363,  60, 1, 8),

    # ── Tier 1 Large Cities (weight 4–6) ────────────────────────────────────
    ("Pune",          "Maharashtra",    18.520,  73.856,  45, 1, 6),
    ("Ahmedabad",     "Gujarat",        23.022,  72.571,  45, 1, 6),
    ("Surat",         "Gujarat",        21.170,  72.831,  45, 1, 4),
    ("Jaipur",        "Rajasthan",      26.912,  75.787,  45, 1, 4),

    # ── Tier 2 Cities (weight 3–4) ──────────────────────────────────────────
    ("Lucknow",       "Uttar Pradesh",  26.846,  80.946,  35, 2, 4),
    ("Nagpur",        "Maharashtra",    21.145,  79.088,  35, 2, 3),
    ("Indore",        "Madhya Pradesh", 22.719,  75.857,  35, 2, 3),
    ("Bhopal",        "Madhya Pradesh", 23.259,  77.412,  35, 2, 3),
    ("Patna",         "Bihar",          25.594,  85.137,  35, 2, 3),

    # ── Tier 3 / Smaller (weight 2) ─────────────────────────────────────────
    ("Coimbatore",    "Tamil Nadu",     11.017,  76.966,  25, 3, 2),
    ("Kochi",         "Kerala",          9.931,  76.267,  25, 3, 2),
    ("Chandigarh",    "Punjab",         30.733,  76.779,  25, 3, 2),
    ("Guwahati",      "Assam",          26.144,  91.736,  25, 3, 2),
    ("Bhubaneswar",   "Odisha",         20.296,  85.824,  25, 3, 2),

    # ── 5 New Cities ────────────────────────────────────────────────────────
    ("Visakhapatnam", "Andhra Pradesh", 17.686,  83.218,  30, 2, 3),  # southeast coast gap
    ("Vadodara",      "Gujarat",        22.307,  73.181,  30, 2, 3),  # central Gujarat gap
    ("Amritsar",      "Punjab",         31.634,  74.872,  25, 3, 2),  # far northwest
    ("Varanasi",      "Uttar Pradesh",  25.317,  82.973,  25, 3, 2),  # east UP corridor
    ("Mangaluru",     "Karnataka",      12.914,  74.856,  25, 3, 2),  # southwest coast gap
]

# Build a weighted city list for sampling
city_names    = [c[0] for c in CITIES]
city_weights  = [c[6] for c in CITIES]
city_lookup   = {c[0]: c for c in CITIES}

def pick_city():
    return random.choices(city_names, weights=city_weights, k=1)[0]

def jittered_coords(city_name, jitter_km=8):
    """Return (lat, lon) near city center with random offset up to jitter_km."""
    c = city_lookup[city_name]
    lat_c, lon_c = c[2], c[3]
    # 1 degree latitude ≈ 111 km everywhere
    # 1 degree longitude ≈ 111 * cos(lat) km
    jitter_lat = (random.uniform(-jitter_km, jitter_km)) / 111.0
    jitter_lon = (random.uniform(-jitter_km, jitter_km)) / (111.0 * np.cos(np.radians(lat_c)))
    return round(lat_c + jitter_lat, 6), round(lon_c + jitter_lon, 6)

def make_record(entity_type, prefix, index, city_name=None):
    if city_name is None:
        city_name = pick_city()
    city_data = city_lookup[city_name]
    lat, lon   = jittered_coords(city_name)
    return {
        "id":              f"{prefix}-{str(index).zfill(4)}",
        "name":            f"{fake.company()} {entity_type}",
        "type":            entity_type,
        "city":            city_name,
        "state":           city_data[1],
        "address":         fake.address().replace("\n", ", "),
        "pin_code":        fake.postcode(),
        "contact_person":  fake.name(),
        "phone":           fake.phone_number(),
        "latitude":        lat,
        "longitude":       lon,
        "active":          random.random() < 0.95,   # 95% active
    }

# ── Generate each entity type ───────────────────────────────────────────────
records = []

# Mother Warehouses (18) — spread across major metros only
mw_cities = ["Mumbai","Delhi","Bengaluru","Chennai","Hyderabad",
              "Kolkata","Pune","Ahmedabad","Surat","Jaipur",
              "Lucknow","Nagpur","Indore","Bhopal","Patna",
              "Coimbatore","Kochi","Guwahati"]
for i, city in enumerate(mw_cities, 1):
    records.append(make_record("Mother Warehouse", "MW", i, city))

# Additional Warehouses (55)
for i in range(1, 56):
    records.append(make_record("Additional Warehouse", "AW", i))

# Retail Offices (180)
for i in range(1, 181):
    records.append(make_record("Retail Office", "RO", i))

# Dealers (700)
for i in range(1, 701):
    records.append(make_record("Dealer", "DLR", i))

# Independent Workshops (4500)
for i in range(1, 4501):
    records.append(make_record("Independent Workshop", "IW", i))

# MASS (400)
for i in range(1, 401):
    records.append(make_record("MASS", "MASS", i))

# ── Save ────────────────────────────────────────────────────────────────────
os.makedirs("../data/raw", exist_ok=True)
df = pd.DataFrame(records)
df.to_csv("../data/raw/locations.csv", index=False)
print(f"Generated {len(df)} location records → ../data/raw/locations.csv")

# Also save city reference for use in validation (Step 4)
city_ref = pd.DataFrame([{
    "city": c[0], "state": c[1], "center_lat": c[2], "center_lon": c[3],
    "allowed_radius_km": c[4], "tier": c[5]
} for c in CITIES])
city_ref.to_csv("../data/raw/city_reference.csv", index=False)
print(f"Saved city reference → ../data/raw/city_reference.csv")