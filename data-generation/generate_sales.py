import pandas as pd
import numpy as np
import random
from datetime import date, timedelta
import os

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

city_weight_map = {c[0]: c[6] for c in CITIES}

PARTS_CATEGORIES = [
    "Engine Parts", "Brakes", "Electrical", "Suspension",
    "Body Parts", "Filters & Fluids", "Transmission", "Cooling System"
]

def random_date(start=date(2020, 1, 1), end=date(2024, 12, 31)):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def revenue_for_dealer(dealer_city):
    weight   = city_weight_map.get(dealer_city, 2)
    # weight 12 (Mumbai/Delhi) → mean ~8.4L | weight 2 (small city) → mean ~1.5L
    mean_rev = 150_000 + (weight / 12) * 1_350_000
    std_rev  = mean_rev * 0.4
    revenue  = np.random.normal(mean_rev, std_rev)
    return round(float(np.clip(revenue, 50_000, 1_500_000)), 2)

# Load dealer IDs and their cities from locations file
locations_df    = pd.read_csv("../data/raw/locations.csv")
dealer_rows     = locations_df[locations_df["type"] == "Dealer"]
dealer_city_map = dealer_rows.set_index("id")["city"].to_dict()
dealers         = dealer_rows["id"].tolist()

records = []
for dealer_id in dealers:
    city        = dealer_city_map.get(dealer_id, "Mumbai")
    n_records   = random.randint(20, 28)
    for _ in range(n_records):
        records.append({
            "dealer_id":      dealer_id,
            "sale_date":      random_date(),
            "parts_category": random.choice(PARTS_CATEGORIES),
            "units_sold":     random.randint(10, 500),
            "revenue_inr":    revenue_for_dealer(city),
        })

os.makedirs("../data/raw", exist_ok=True)
df = pd.DataFrame(records)
df.to_csv("../data/raw/sales_history.csv", index=False)
print(f"Generated {len(df):,} sales records → ../data/raw/sales_history.csv")

# Quick sanity check — print mean revenue by city tier
locations_df["tier"] = locations_df["city"].map({c[0]: c[5] for c in CITIES})
dealer_with_tier     = dealer_rows.merge(
    df.groupby("dealer_id")["revenue_inr"].mean().reset_index(),
    left_on="id", right_on="dealer_id"
)
print("\nMean revenue per record by tier (sanity check):")
print(dealer_with_tier.groupby(
    dealer_with_tier["city"].map({c[0]: c[5] for c in CITIES})
)["revenue_inr"].mean().rename("mean_revenue_inr").to_string())