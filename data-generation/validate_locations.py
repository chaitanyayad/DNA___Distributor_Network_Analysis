import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import random
import os
from pathlib import Path

random.seed(42)
np.random.seed(42)

ROOT = Path(__file__).parent.parent
os.makedirs(ROOT / "data/processed", exist_ok=True)

# ── Load data ────────────────────────────────────────────────────────────────
df       = pd.read_csv(ROOT / "data/raw/locations.csv")
city_ref = pd.read_csv(ROOT / "data/raw/city_reference.csv")
india    = gpd.read_file(ROOT / "data/raw/india_states.geojson")

india_union = india.union_all() if hasattr(india, 'union_all') else india.unary_union

india["state_upper"] = india["NAME_1"].str.strip().str.title()
state_geoms          = india.set_index("state_upper")["geometry"].to_dict()

city_lookup = city_ref.set_index("city").to_dict("index")

# ── Tracking columns ─────────────────────────────────────────────────────────
df["coord_validation_status"] = "PASS"
df["validation_note"]         = ""

total_input = len(df)
log_rows    = []

# ── LAYER 1: National bounding box ───────────────────────────────────────────
print("Running Layer 1 — national bounding box check...")

l1_mask = (
    (df["latitude"]  < 6.0)  | (df["latitude"]  > 37.6) |
    (df["longitude"] < 68.0) | (df["longitude"] > 97.5)
)
l1_fail = df[l1_mask].index.tolist()
df.loc[l1_mask, "coord_validation_status"] = "DROPPED"
df.loc[l1_mask, "validation_note"]         = "Layer1: outside India bounding box"

print(f"  Layer 1 failures : {len(l1_fail)}")
log_rows.append({
    "layer":     "Layer 1 — bounding box",
    "checked":   total_input,
    "failed":    len(l1_fail),
    "corrected": 0,
    "dropped":   len(l1_fail),
    "note":      "Outside lat 6–37.6 / lon 68–97.5"
})

working = df[df["coord_validation_status"] == "PASS"].copy()

# ── LAYER 2: City radius check ───────────────────────────────────────────────
print("Running Layer 2 — city radius check...")

def dist_km(lat1, lon1, lat2, lon2):
    return np.sqrt(
        ((lat1 - lat2) * 111) ** 2 +
        ((lon1 - lon2) * 111 * np.cos(np.radians(lat1))) ** 2
    )

def jittered_coords(city_name, jitter_km=4):
    c        = city_lookup[city_name]
    lat_c    = c["center_lat"]
    lon_c    = c["center_lon"]
    jitter_lat = random.uniform(-jitter_km, jitter_km) / 111.0
    jitter_lon = random.uniform(-jitter_km, jitter_km) / (
        111.0 * np.cos(np.radians(lat_c))
    )
    return round(lat_c + jitter_lat, 6), round(lon_c + jitter_lon, 6)

l2_fail = l2_corrected = l2_dropped = 0

for idx, row in working.iterrows():
    city = row["city"]
    if city not in city_lookup:
        df.loc[idx, "coord_validation_status"] = "DROPPED"
        df.loc[idx, "validation_note"]         = "Layer2: UNKNOWN_CITY"
        l2_fail    += 1
        l2_dropped += 1
        continue

    c       = city_lookup[city]
    dist    = dist_km(row["latitude"], row["longitude"],
                      c["center_lat"], c["center_lon"])
    allowed = c["allowed_radius_km"]

    if dist > allowed:
        l2_fail += 1
        corrected = False
        for attempt in range(3):
            new_lat, new_lon = jittered_coords(city, jitter_km=4 - attempt)
            new_dist = dist_km(new_lat, new_lon, c["center_lat"], c["center_lon"])
            if new_dist <= allowed:
                df.loc[idx, "latitude"]                = new_lat
                df.loc[idx, "longitude"]               = new_lon
                df.loc[idx, "coord_validation_status"] = "CORRECTED"
                df.loc[idx, "validation_note"]         = (
                    f"Layer2: corrected attempt {attempt+1}, "
                    f"new dist {new_dist:.1f}km"
                )
                l2_corrected += 1
                corrected = True
                break
        if not corrected:
            df.loc[idx, "coord_validation_status"] = "DROPPED"
            df.loc[idx, "validation_note"]         = (
                f"Layer2: failed after 3 retries, dist {dist:.1f}km"
            )
            l2_dropped += 1

print(f"  Layer 2 failures : {l2_fail}")
print(f"  Auto-corrected   : {l2_corrected}")
print(f"  Dropped          : {l2_dropped}")
log_rows.append({
    "layer":     "Layer 2 — city radius",
    "checked":   len(working),
    "failed":    l2_fail,
    "corrected": l2_corrected,
    "dropped":   l2_dropped,
    "note":      "Distance from city center exceeds allowed radius"
})

working = df[df["coord_validation_status"].isin(["PASS", "CORRECTED"])].copy()

# ── LAYER 3: State boundary polygon check ────────────────────────────────────
print("Running Layer 3 — state boundary polygon check...")

# Map our state names to GeoJSON NAME_1 values
STATE_MAP = {
    "Andhra Pradesh":  "Andhra Pradesh",
    "Assam":           "Assam",
    "Bihar":           "Bihar",
    "Delhi":           "Nct Of Delhi",
    "Gujarat":         "Gujarat",
    "Karnataka":       "Karnataka",
    "Kerala":          "Kerala",
    "Madhya Pradesh":  "Madhya Pradesh",
    "Maharashtra":     "Maharashtra",
    "Odisha":          "Odisha",
    "Punjab":          "Punjab",
    "Rajasthan":       "Rajasthan",
    "Tamil Nadu":      "Tamil Nadu",
    "Telangana":       "Telangana",
    "Uttar Pradesh":   "Uttar Pradesh",
    "West Bengal":     "West Bengal",
}

l3_fail = l3_corrected = l3_dropped = 0

for idx, row in working.iterrows():
    point     = Point(row["longitude"], row["latitude"])
    our_state = row["state"]
    shp_state = STATE_MAP.get(our_state, our_state)

    if not india_union.contains(point):
        df.loc[idx, "coord_validation_status"] = "DROPPED"
        df.loc[idx, "validation_note"]         = "Layer3: OFFSHORE"
        l3_fail    += 1
        l3_dropped += 1
        continue

    if shp_state in state_geoms:
        if not state_geoms[shp_state].contains(point):
            actual_state = "Unknown"
            for sname, sgeom in state_geoms.items():
                if sgeom.contains(point):
                    actual_state = sname
                    break

            l3_fail += 1
            if actual_state != "Unknown":
                df.loc[idx, "state"]                   = actual_state
                df.loc[idx, "coord_validation_status"] = "CORRECTED"
                df.loc[idx, "validation_note"]         = (
                    f"Layer3: STATE_MISMATCH — "
                    f"was {our_state}, corrected to {actual_state}"
                )
                l3_corrected += 1
            else:
                df.loc[idx, "coord_validation_status"] = "DROPPED"
                df.loc[idx, "validation_note"]         = "Layer3: not in any state polygon"
                l3_dropped += 1

print(f"  Layer 3 failures : {l3_fail}")
print(f"  State corrected  : {l3_corrected}")
print(f"  Dropped          : {l3_dropped}")
log_rows.append({
    "layer":     "Layer 3 — state boundary",
    "checked":   len(working),
    "failed":    l3_fail,
    "corrected": l3_corrected,
    "dropped":   l3_dropped,
    "note":      "Point-in-polygon against India state boundaries"
})

working = df[df["coord_validation_status"].isin(["PASS", "CORRECTED"])].copy()

# ── LAYER 4: Missing values, formatting, duplicates ──────────────────────────
print("Running Layer 4 — missing values, formatting, duplicates...")

l4_dropped = 0

critical_missing = working[
    working["latitude"].isna() |
    working["longitude"].isna() |
    working["type"].isna()
].index.tolist()
df.loc[critical_missing, "coord_validation_status"] = "DROPPED"
df.loc[critical_missing, "validation_note"]         = "Layer4: missing lat/lon/type"
l4_dropped += len(critical_missing)

for col in ["contact_person", "phone", "address"]:
    df[col] = df[col].fillna("Unknown")

df["city"]  = df["city"].str.strip().str.title()
df["state"] = df["state"].str.strip().str.title()
df["type"]  = df["type"].str.strip()

dupes = df[df.duplicated(subset=["id"], keep="first")].index.tolist()
df.loc[dupes, "coord_validation_status"] = "DROPPED"
df.loc[dupes, "validation_note"]         = "Layer4: duplicate ID"
l4_dropped += len(dupes)

working2    = df[df["coord_validation_status"].isin(["PASS", "CORRECTED"])].copy()
coord_dupes = working2[
    working2.duplicated(subset=["latitude", "longitude"], keep="first")
].index.tolist()
df.loc[coord_dupes, "coord_validation_status"] = "DROPPED"
df.loc[coord_dupes, "validation_note"]         = "Layer4: near-duplicate coordinates"
l4_dropped += len(coord_dupes)

print(f"  Layer 4 dropped  : {l4_dropped}")
log_rows.append({
    "layer":     "Layer 4 — missing values / duplicates",
    "checked":   len(working),
    "failed":    l4_dropped,
    "corrected": 0,
    "dropped":   l4_dropped,
    "note":      "Missing critical fields, duplicate IDs, near-duplicate coords"
})

# ── Final clean dataset ───────────────────────────────────────────────────────
final = df[df["coord_validation_status"].isin(["PASS", "CORRECTED"])].copy()

final.to_csv(ROOT / "data/processed/locations_clean.csv", index=False)
print(f"\nClean dataset → data/processed/locations_clean.csv")

# ── Validation log ────────────────────────────────────────────────────────────
total_dropped   = len(df[df["coord_validation_status"] == "DROPPED"])
total_corrected = len(df[df["coord_validation_status"] == "CORRECTED"])
total_final     = len(final)

summary = pd.DataFrame(log_rows)
summary.to_csv(ROOT / "data/processed/validation_log.csv", index=False)

print(f"\n{'='*50}")
print(f"VALIDATION SUMMARY")
print(f"{'='*50}")
print(f"Total input          : {total_input:,}")
print(f"Total dropped        : {total_dropped:,}")
print(f"Total corrected      : {total_corrected:,}")
print(f"Final clean records  : {total_final:,}")
print(f"\nValidation log → data/processed/validation_log.csv")
print(f"\nLayer-by-layer:")
print(summary.to_string(index=False))
print(f"\nStatus breakdown:")
print(df["coord_validation_status"].value_counts().to_string())