

import pandas as pd
import numpy as np
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)
np.random.seed(42)

# City → tier mapping (must match generate_locations.py CITIES list)
CITY_TIER = {
    "Mumbai": 1, "Delhi": 1, "Bengaluru": 1, "Chennai": 1,
    "Hyderabad": 1, "Kolkata": 1,
    "Pune": 1, "Ahmedabad": 1, "Surat": 1, "Jaipur": 1,
    "Lucknow": 2, "Nagpur": 2, "Indore": 2, "Bhopal": 2, "Patna": 2,
    "Visakhapatnam": 2, "Vadodara": 2,
    "Coimbatore": 3, "Kochi": 3, "Chandigarh": 3, "Guwahati": 3,
    "Bhubaneswar": 3, "Amritsar": 3, "Varanasi": 3, "Mangaluru": 3,
}

# Revenue mean (₹) per tier — city-tier dependent for ML signal
REVENUE_MEAN = {1: 840_000, 2: 510_000, 3: 370_000}
REVENUE_STD  = {1: 200_000, 2: 130_000, 3:  90_000}

PARTS_CATEGORIES = [
    "Engine Parts", "Brakes", "Electrical", "Suspension",
    "Transmission", "Body Parts", "Filters", "Tyres & Wheels",
]

START_DATE = date(2020, 1, 1)
END_DATE   = date(2024, 12, 31)


def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def generate_dealer_sales(dealer_id, city, n_records=24):
    tier = CITY_TIER.get(city, 2)
    mu   = REVENUE_MEAN[tier]
    sig  = REVENUE_STD[tier]
    rows = []
    for _ in range(n_records):
        revenue = max(50_000, round(np.random.normal(mu, sig), -3))
        rows.append({
            "dealer_id":      dealer_id,
            "city":           city,
            "sale_date":      random_date(START_DATE, END_DATE).isoformat(),
            "parts_category": random.choice(PARTS_CATEGORIES),
            "units_sold":     random.randint(10, 500),
            "revenue_inr":    int(revenue),
        })
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Load dealer list from already-generated locations.csv
# ─────────────────────────────────────────────────────────────────────────────
raw_dir = Path(__file__).parent.parent / "data" / "raw"
locations_path = raw_dir / "locations.csv"

if not locations_path.exists():
    raise FileNotFoundError(
        f"locations.csv not found at {locations_path}\n"
        "Run generate_locations.py first."
    )

locs    = pd.read_csv(locations_path)
dealers = locs[locs["type"] == "Dealer"][["id", "city"]].reset_index(drop=True)
print(f"Found {len(dealers)} dealers in locations.csv")

# ─────────────────────────────────────────────────────────────────────────────
# Generate sales — ~24 records per dealer = ~16,800 total
# ─────────────────────────────────────────────────────────────────────────────
all_records = []
for _, row in dealers.iterrows():
    n = random.randint(20, 28)   # slight variance, avg ~24
    all_records.extend(generate_dealer_sales(row["id"], row["city"], n))

df = pd.DataFrame(all_records)

out_path = raw_dir / "sales_history.csv"
df.to_csv(out_path, index=False)
print(f"Generated {len(df)} sales records → {out_path}")
print(f"Revenue by tier sample:\n{df.groupby('city')['revenue_inr'].mean().sort_values(ascending=False).head(10)}")