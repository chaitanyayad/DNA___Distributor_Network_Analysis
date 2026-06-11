

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PATHS — all relative to this file, not the working directory
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent.parent
RAW_DIR      = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE CONNECTION
# Strips +asyncpg from DATABASE_URL — psycopg2 needs plain postgresql://
# FastAPI uses postgresql+asyncpg:// — both coexist via this strip
# ─────────────────────────────────────────────────────────────────────────────
env_path = BASE_DIR / "backend" / ".env"
load_dotenv(env_path)

raw_url = os.getenv("DATABASE_URL", "")
if not raw_url:
    print("ERROR: DATABASE_URL not found in backend/.env")
    print(f"Looked for .env at: {env_path}")
    sys.exit(1)

# Strip +asyncpg so psycopg2 can connect
db_url = raw_url.replace("postgresql+asyncpg://", "postgresql://")

try:
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()
    print(f"Connected to database")
except Exception as e:
    print(f"ERROR: Could not connect to database: {e}")
    print(f"URL used: {db_url}")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────────────────────
def load_csv(filename):
    path = PROCESSED_DIR / filename if (PROCESSED_DIR / filename).exists() \
           else RAW_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    df = pd.read_csv(path)
    print(f"  Loaded {len(df):,} rows from {path.name}")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 1. USERS
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Loading users ────────────────────────────────────────────────")
df_users = load_csv("users.csv")
df_users["distributor_id"] = df_users["distributor_id"].where(
    df_users["distributor_id"].notna(), None
)

cur.execute("TRUNCATE TABLE users CASCADE")

user_rows = [
    (
        row["id"],
        row["username"],
        row["email"],
        row["hashed_password"],
        row["role"],
        row["distributor_id"] if pd.notna(row["distributor_id"]) else None,
    )
    for _, row in df_users.iterrows()
]

execute_batch(cur, """
    INSERT INTO users (id, username, email, hashed_password, role, distributor_id)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO NOTHING
""", user_rows)

conn.commit()
print(f"  ✓ Inserted {len(user_rows)} users")


# ─────────────────────────────────────────────────────────────────────────────
# 2. LOCATIONS
# Use locations_clean.csv if validation has been run; fallback to locations.csv
# ST_MakePoint(longitude, latitude) — longitude FIRST, latitude SECOND
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Loading locations ────────────────────────────────────────────")
try:
    df_loc = load_csv("locations_clean.csv")
    print("  Using validated locations_clean.csv")
except FileNotFoundError:
    df_loc = load_csv("locations.csv")
    print("  WARNING: locations_clean.csv not found, using raw locations.csv")
    print("  Run validate_locations.py (Step 4) before this for clean data")

cur.execute("TRUNCATE TABLE locations CASCADE")

loc_rows = []
skipped  = 0
for _, row in df_loc.iterrows():
    try:
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        # Basic India bounds check — belt-and-suspenders after validation
        if not (6.0 <= lat <= 37.6 and 68.0 <= lon <= 97.5):
            skipped += 1
            continue
        loc_rows.append((
            row["id"],
            row["name"],
            row["type"],
            row.get("city"),
            row.get("state"),
            row.get("address"),
            row.get("pin_code"),
            row.get("contact_person"),
            row.get("phone"),
            bool(row.get("active", True)),
            lon,   # longitude FIRST for ST_MakePoint
            lat,   # latitude SECOND
        ))
    except (ValueError, TypeError):
        skipped += 1

if skipped:
    print(f"  Skipped {skipped} rows with bad coordinates")

execute_batch(cur, """
    INSERT INTO locations
        (id, name, type, city, state, address, pin_code,
         contact_person, phone, active, geom)
    VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        ST_SetSRID(ST_MakePoint(%s, %s), 4326)
    )
    ON CONFLICT (id) DO NOTHING
""", loc_rows, page_size=500)

conn.commit()
print(f"  ✓ Inserted {len(loc_rows)} locations")


# ─────────────────────────────────────────────────────────────────────────────
# 3. MARKET POTENTIAL GRID
# Large file — load in chunks of 10,000 rows to avoid memory issues
# predicted_revenue_inr and hotspot_score left NULL — Step 5 (ML) fills them
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Loading vehicle grid ─────────────────────────────────────────")
grid_path = RAW_DIR / "vehicle_grid.csv"
if not grid_path.exists():
    print("  WARNING: vehicle_grid.csv not found — skipping grid load")
    print("  Run generate_vehicle_grid.py first")
else:
    cur.execute("TRUNCATE TABLE market_potential_grid CASCADE")
    conn.commit()

    CHUNK_SIZE  = 10_000
    total_rows  = 0
    skipped_grid = 0

    for chunk_df in pd.read_csv(grid_path, chunksize=CHUNK_SIZE):
        grid_rows = []
        for _, row in chunk_df.iterrows():
            try:
                lat = float(row["center_lat"])
                lon = float(row["center_lon"])
                if not (6.0 <= lat <= 37.6 and 68.0 <= lon <= 97.5):
                    skipped_grid += 1
                    continue
                grid_rows.append((
                    row["grid_id"],
                    int(row["vehicle_count"]),
                    float(row["avg_vehicle_age"]),
                    float(row["commercial_pct"]),
                    float(row["weighted_score"]),
                    lon,   # longitude FIRST for ST_MakePoint
                    lat,
                ))
            except (ValueError, TypeError):
                skipped_grid += 1

        execute_batch(cur, """
            INSERT INTO market_potential_grid
                (grid_id, vehicle_count, avg_vehicle_age,
                 commercial_pct, weighted_score, geom)
            VALUES (
                %s, %s, %s, %s, %s,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)
            )
            ON CONFLICT (grid_id) DO NOTHING
        """, grid_rows, page_size=1000)

        conn.commit()
        total_rows += len(grid_rows)
        print(f"  ...{total_rows:,} grid rows loaded", end="\r")

    print(f"\n  ✓ Inserted {total_rows:,} grid cells (skipped {skipped_grid})")


# ─────────────────────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Row counts in database ───────────────────────────────────────")
for table in ["users", "locations", "market_potential_grid",
              "distributor_territories", "ro_requests"]:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    print(f"  {table:<30} {count:>10,}")

cur.close()
conn.close()
print("\n✓ Load complete")