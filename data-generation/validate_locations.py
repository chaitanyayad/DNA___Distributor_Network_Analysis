

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path

BASE_DIR       = Path(__file__).parent.parent
RAW_DIR        = BASE_DIR / "data" / "raw"
PROCESSED_DIR  = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# India bounding box
INDIA_LAT_MIN, INDIA_LAT_MAX = 6.0,  37.6
INDIA_LON_MIN, INDIA_LON_MAX = 68.0, 97.5


# ─────────────────────────────────────────────────────────────────────────────
# LOAD INPUT FILES
# ─────────────────────────────────────────────────────────────────────────────
print("Loading locations.csv ...")
df = pd.read_csv(RAW_DIR / "locations.csv")
print(f"  {len(df):,} rows loaded")

print("Loading city_reference.csv ...")
city_ref = pd.read_csv(RAW_DIR / "city_reference.csv")
city_lookup = {
    row["city"]: {
        "state":      row["state"],
        "center_lat": row["center_lat"],
        "center_lon": row["center_lon"],
        "radius_km":  row["allowed_radius_km"],
        "tier":       row["tier"],
    }
    for _, row in city_ref.iterrows()
}

print("Loading india_states.geojson ...")
geojson_path = RAW_DIR / "india_states.geojson"
if not geojson_path.exists():
    print(f"\nERROR: india_states.geojson not found at {geojson_path}")
    print("Download it from:")
    print("  https://github.com/datameet/maps/raw/master/States/Admin2.geojson")
    print("Save it to: data/raw/india_states.geojson")
    raise SystemExit(1)

india_states = gpd.read_file(geojson_path)

# FIX: Column in this GeoJSON is NAME_1, not ST_NM
# Print actual columns so you know what you're working with
print(f"  GeoJSON columns: {list(india_states.columns)}")

# Detect which column holds state names
state_col = None
for candidate in ["NAME_1", "ST_NM", "state", "State", "NAME", "name"]:
    if candidate in india_states.columns:
        state_col = candidate
        break

if state_col is None:
    print(f"ERROR: Cannot find state name column in GeoJSON.")
    print(f"Available columns: {list(india_states.columns)}")
    raise SystemExit(1)

print(f"  Using column '{state_col}' for state names")
india_states = india_states.rename(columns={state_col: "state_name"})

# Build a dict: state_name → polygon for fast lookup
state_polygons = {
    row["state_name"]: row["geometry"]
    for _, row in india_states.iterrows()
    if row["geometry"] is not None
}
print(f"  {len(state_polygons)} state polygons loaded")

# ─────────────────────────────────────────────────────────────────────────────
# INITIALISE TRACKING COLUMNS
# ─────────────────────────────────────────────────────────────────────────────
df["coord_validation_status"] = "OK"
df["drop_reason"] = ""

log = {
    "input_total":          len(df),
    "layer1_dropped":       0,
    "layer2_failed":        0,
    "layer2_corrected":     0,
    "layer2_dropped":       0,
    "layer3_state_mismatch": 0,
    "layer3_offshore":      0,
    "layer3_corrected":     0,
    "layer4_missing_dropped": 0,
    "layer4_duplicates_dropped": 0,
    "final_clean":          0,
}


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 1 — National Bounding Box Check
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Layer 1: India bounding box ──────────────────────────────────")

def outside_india(row):
    try:
        lat, lon = float(row["latitude"]), float(row["longitude"])
        return not (INDIA_LAT_MIN <= lat <= INDIA_LAT_MAX and
                    INDIA_LON_MIN <= lon <= INDIA_LON_MAX)
    except (ValueError, TypeError):
        return True

mask_l1 = df.apply(outside_india, axis=1)
df.loc[mask_l1, "coord_validation_status"] = "DROPPED"
df.loc[mask_l1, "drop_reason"] = "LAYER1_BBOX_FAIL"
log["layer1_dropped"] = int(mask_l1.sum())
print(f"  Dropped: {log['layer1_dropped']} rows outside India bounding box")


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2 — City Radius Check
# Skip rows already dropped. Skip rural workshop rows (city='Rural').
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Layer 2: City radius check ───────────────────────────────────")

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (np.sin(dlat/2)**2 +
         np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2)
    return R * 2 * np.arcsin(np.sqrt(a))


active = df[df["coord_validation_status"] == "OK"].copy()
rural_mask = active["city"] == "Rural"
city_active = active[~rural_mask]

for idx, row in city_active.iterrows():
    city = row["city"]
    if city not in city_lookup:
        df.at[idx, "coord_validation_status"] = "UNKNOWN_CITY"
        continue

    ref   = city_lookup[city]
    dist  = haversine_km(
        float(row["latitude"]),  float(row["longitude"]),
        ref["center_lat"],       ref["center_lon"]
    )

    if dist > ref["radius_km"]:
        log["layer2_failed"] += 1

        # Attempt auto-correction — regenerate with smaller jitter (max 3 tries)
        corrected = False
        for attempt in range(3):
            small_jitter_km = ref["radius_km"] * 0.4
            jitter_lat = np.random.uniform(-small_jitter_km, small_jitter_km) / 111.0
            jitter_lon = np.random.uniform(-small_jitter_km, small_jitter_km) / (
                111.0 * np.cos(np.radians(ref["center_lat"]))
            )
            new_lat = round(ref["center_lat"] + jitter_lat, 6)
            new_lon = round(ref["center_lon"] + jitter_lon, 6)
            new_dist = haversine_km(new_lat, new_lon, ref["center_lat"], ref["center_lon"])
            if new_dist <= ref["radius_km"]:
                df.at[idx, "latitude"]  = new_lat
                df.at[idx, "longitude"] = new_lon
                df.at[idx, "coord_validation_status"] = "CORRECTED"
                log["layer2_corrected"] += 1
                corrected = True
                break

        if not corrected:
            df.at[idx, "coord_validation_status"] = "DROPPED"
            df.at[idx, "drop_reason"] = "LAYER2_CITY_RADIUS_FAIL"
            log["layer2_dropped"] += 1

print(f"  Failed radius check:  {log['layer2_failed']}")
print(f"  Auto-corrected:       {log['layer2_corrected']}")
print(f"  Dropped after 3 tries:{log['layer2_dropped']}")


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 3 — State Boundary Polygon Check
# Checks point is on land and in correct state.
# Rural workshops: only check they're inside India (any state polygon).
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Layer 3: State boundary polygon check ────────────────────────")

# Build a unified India polygon for rural workshop checks
india_union = india_states.geometry.union_all()

active_l3 = df[df["coord_validation_status"].isin(["OK", "CORRECTED"])].copy()

for idx, row in active_l3.iterrows():
    try:
        point = Point(float(row["longitude"]), float(row["latitude"]))
    except (ValueError, TypeError):
        df.at[idx, "coord_validation_status"] = "DROPPED"
        df.at[idx, "drop_reason"] = "LAYER3_INVALID_COORDS"
        continue

    city = str(row.get("city", ""))

    if city == "Rural":
        # Rural workshops: only check they're inside India at all
        if not india_union.contains(point):
            df.at[idx, "coord_validation_status"] = "DROPPED"
            df.at[idx, "drop_reason"] = "LAYER3_OFFSHORE"
            log["layer3_offshore"] += 1
        # If inside India → keep as-is (no city/state constraint for rural)
        continue

    # City-based records: check correct state polygon
    expected_state = row.get("state", "")
    matched_state  = None

    for state_name, polygon in state_polygons.items():
        if polygon.contains(point):
            matched_state = state_name
            break

    if matched_state is None:
        # Point not inside any state polygon → offshore or outside India
        df.at[idx, "coord_validation_status"] = "DROPPED"
        df.at[idx, "drop_reason"] = "LAYER3_OFFSHORE"
        log["layer3_offshore"] += 1

    elif matched_state.lower() != str(expected_state).lower():
        # Inside India but wrong state — correct the state field, keep the point
        df.at[idx, "state"] = matched_state
        df.at[idx, "coord_validation_status"] = "CORRECTED"
        log["layer3_state_mismatch"] += 1
        log["layer3_corrected"] += 1

print(f"  State mismatches corrected: {log['layer3_state_mismatch']}")
print(f"  Offshore/outside India:     {log['layer3_offshore']}")


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 4 — Missing Values and Duplicates
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Layer 4: Missing values and duplicates ───────────────────────")

# Work only on surviving rows
clean = df[~df["coord_validation_status"].isin(["DROPPED"])].copy()

# Drop rows missing the three essential fields
essential_missing = (
    clean["latitude"].isna() |
    clean["longitude"].isna() |
    clean["type"].isna()
)
log["layer4_missing_dropped"] = int(essential_missing.sum())
clean = clean[~essential_missing]

# Fill non-essential missing fields
for col in ["contact_person", "phone", "address"]:
    if col in clean.columns:
        clean[col] = clean[col].fillna("Unknown")

# Text standardisation
clean["city"]  = clean["city"].str.strip().str.title()
clean["state"] = clean["state"].str.strip().str.title()
clean["type"]  = clean["type"].str.strip()   # preserve exact case for DB

# Duplicate ID check — keep first occurrence
before_dedup = len(clean)
clean = clean.drop_duplicates(subset=["id"], keep="first")
log["layer4_duplicates_dropped"] = before_dedup - len(clean)

print(f"  Missing essential fields dropped: {log['layer4_missing_dropped']}")
print(f"  Duplicate IDs dropped:            {log['layer4_duplicates_dropped']}")


# ─────────────────────────────────────────────────────────────────────────────
# WRITE OUTPUTS
# ─────────────────────────────────────────────────────────────────────────────
log["final_clean"] = len(clean)

clean_out = PROCESSED_DIR / "locations_clean.csv"
clean.to_csv(clean_out, index=False)
print(f"\n✓ Wrote {len(clean):,} clean records → {clean_out}")

# Validation log
log_df = pd.DataFrame([{
    "step":    k,
    "count":   v,
} for k, v in log.items()])
log_out = PROCESSED_DIR / "validation_log.csv"
log_df.to_csv(log_out, index=False)
print(f"✓ Validation log → {log_out}")

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Validation Summary ───────────────────────────────────────────")
print(f"  Input records         : {log['input_total']:>7,}")
print(f"  Layer 1 dropped       : {log['layer1_dropped']:>7,}")
print(f"  Layer 2 failed        : {log['layer2_failed']:>7,}  ({log['layer2_corrected']} corrected, {log['layer2_dropped']} dropped)")
print(f"  Layer 3 offshore      : {log['layer3_offshore']:>7,}")
print(f"  Layer 3 state fix     : {log['layer3_state_mismatch']:>7,}")
print(f"  Layer 4 dropped       : {log['layer4_missing_dropped'] + log['layer4_duplicates_dropped']:>7,}")
print(f"  ─────────────────────────────")
print(f"  Final clean records   : {log['final_clean']:>7,}")