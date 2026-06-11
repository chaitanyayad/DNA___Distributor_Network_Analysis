

import os
import pickle
import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from sklearn.cluster import DBSCAN
from sklearn.neighbors import BallTree
from dotenv import load_dotenv
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
DBSCAN_EPS_KM      = 5.0                        # workshops within 5 km → same cluster
DBSCAN_EPS_RAD     = DBSCAN_EPS_KM / 6371.0     # convert to radians for haversine
DBSCAN_MIN_SAMPLES = 5                           # min workshops to form a cluster
DEALER_GAP_KM      = 15.0                        # cluster centroid > 15 km from dealer → white space
GRID_UPDATE_RADIUS = 10_000                      # metres — grid cells within 10 km of centroid get flagged

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent.parent
MODELS_DIR    = Path(__file__).parent / "models"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE CONNECTION
# ─────────────────────────────────────────────────────────────────────────────
env_path = BASE_DIR / "backend" / ".env"
load_dotenv(env_path)

raw_url = os.getenv("DATABASE_URL", "")
if not raw_url:
    raise RuntimeError(f"DATABASE_URL not found in {env_path}")

db_url = raw_url.replace("postgresql+asyncpg://", "postgresql://")

print("Connecting to database...")
conn = psycopg2.connect(db_url)
print("Connected")

# ─────────────────────────────────────────────────────────────────────────────
# LOAD WORKSHOPS AND DEALERS FROM DB
# ST_Y(geom) = latitude, ST_X(geom) = longitude
# ─────────────────────────────────────────────────────────────────────────────
print("\nLoading workshops and dealers from database...")

workshops = pd.read_sql("""
    SELECT id,
           ST_Y(geom) AS latitude,
           ST_X(geom) AS longitude,
           city
    FROM   locations
    WHERE  type   = 'Independent Workshop'
      AND  active = TRUE
""", conn)

dealers = pd.read_sql("""
    SELECT id,
           ST_Y(geom) AS latitude,
           ST_X(geom) AS longitude
    FROM   locations
    WHERE  type   = 'Dealer'
      AND  active = TRUE
""", conn)

print(f"  Workshops: {len(workshops):,}")
print(f"  Dealers  : {len(dealers):,}")

# ─────────────────────────────────────────────────────────────────────────────
# PRE-DBSCAN SANITY CHECK
# Print distance stats so we can immediately see if white spaces are possible
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Sanity check: rural workshop → nearest dealer distances ──────")
rural_ws = workshops[workshops["city"] == "Rural"]
print(f"  Rural workshops: {len(rural_ws):,}")

if len(rural_ws) > 0 and len(dealers) > 0:
    dealer_rad = np.radians(dealers[["latitude", "longitude"]].values)
    tree_check = BallTree(dealer_rad, metric="haversine")

    # Sample up to 1000 rural workshops for the check
    sample = rural_ws.sample(min(1000, len(rural_ws)), random_state=42)
    sample_rad = np.radians(sample[["latitude", "longitude"]].values)
    dists_rad, _ = tree_check.query(sample_rad, k=1)
    dists_km = dists_rad.flatten() * 6371.0

    print(f"  Min distance to nearest dealer : {dists_km.min():.1f} km")
    print(f"  Mean distance to nearest dealer: {dists_km.mean():.1f} km")
    print(f"  Max distance to nearest dealer : {dists_km.max():.1f} km")
    print(f"  Workshops already >{DEALER_GAP_KM:.0f} km from dealer: "
          f"{(dists_km > DEALER_GAP_KM).sum()} / {len(dists_km)}")

    if dists_km.max() < DEALER_GAP_KM:
        print(f"\n  ⚠  WARNING: No rural workshop is more than {DEALER_GAP_KM} km from a dealer.")
        print(f"     White spaces cannot be found with current data.")
        print(f"     Re-run generate_locations.py and reload before continuing.")
    else:
        print(f"\n  ✓ Rural workshops are far enough from dealers — white spaces expected")
print("─────────────────────────────────────────────────────────────────")

# ─────────────────────────────────────────────────────────────────────────────
# DBSCAN CLUSTERING ON ALL WORKSHOPS
# Using haversine metric so distances are computed correctly on a sphere
# eps must be in radians: km / earth_radius_km
# ─────────────────────────────────────────────────────────────────────────────
print(f"\nRunning DBSCAN (eps={DBSCAN_EPS_KM} km, min_samples={DBSCAN_MIN_SAMPLES})...")

workshop_coords_rad = np.radians(workshops[["latitude", "longitude"]].values)

db = DBSCAN(
    eps=DBSCAN_EPS_RAD,
    min_samples=DBSCAN_MIN_SAMPLES,
    algorithm="ball_tree",
    metric="haversine",
    n_jobs=-1,
)
labels = db.fit_predict(workshop_coords_rad)
workshops = workshops.copy()
workshops["cluster_id"] = labels

n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
n_noise    = int((labels == -1).sum())
print(f"  Clusters found : {n_clusters}")
print(f"  Clustered pts  : {int((labels >= 0).sum())}")
print(f"  Noise points   : {n_noise}")

# Save DBSCAN model
dbscan_path = MODELS_DIR / "dbscan_model.pkl"
with open(dbscan_path, "wb") as f:
    pickle.dump(db, f)
print(f"  Model saved → {dbscan_path}")

# ─────────────────────────────────────────────────────────────────────────────
# WHITE SPACE IDENTIFICATION
# For each cluster centroid, check distance to nearest dealer
# ─────────────────────────────────────────────────────────────────────────────
print("\nIdentifying white spaces...")

dealer_coords_rad = np.radians(dealers[["latitude", "longitude"]].values)
dealer_tree       = BallTree(dealer_coords_rad, metric="haversine")

white_spaces = []
clustered    = workshops[workshops["cluster_id"] >= 0]

for cid, group in clustered.groupby("cluster_id"):
    centroid_lat  = group["latitude"].mean()
    centroid_lon  = group["longitude"].mean()
    cluster_size  = len(group)
    rural_count   = int((group["city"] == "Rural").sum())

    # Distance from centroid to nearest dealer
    pt_rad       = np.radians([[centroid_lat, centroid_lon]])
    dist_rad, _  = dealer_tree.query(pt_rad, k=1)
    dist_km      = float(dist_rad[0][0] * 6371.0)

    if dist_km >= DEALER_GAP_KM:
        # Opportunity score: normalised cluster size, capped at 1.0
        opp_score = round(min(cluster_size / 150.0, 1.0), 4)
        white_spaces.append({
            "cluster_id":        int(cid),
            "centroid_lat":      round(centroid_lat, 6),
            "centroid_lon":      round(centroid_lon, 6),
            "cluster_size":      cluster_size,
            "rural_workshops":   rural_count,
            "nearest_dealer_km": round(dist_km, 2),
            "opportunity_score": opp_score,
        })

ws_df = pd.DataFrame(white_spaces)

# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT
# ─────────────────────────────────────────────────────────────────────────────
if ws_df.empty:
    print("\n⚠  No white spaces found.")
    print("   Check the sanity output above — if max distance < 15 km,")
    print("   the data generation fix did not take effect.")
    print("   Re-run: generate_locations.py → validate_locations.py → load_data.py → this script")
else:
    ws_out = PROCESSED_DIR / "whitespaces.csv"
    ws_df.to_csv(ws_out, index=False)

    print(f"\n✓ White spaces found: {len(ws_df)}")
    print(f"  Saved → {ws_out}\n")
    print(ws_df[["cluster_id", "centroid_lat", "centroid_lon",
                 "cluster_size", "nearest_dealer_km", "opportunity_score"]]
          .sort_values("opportunity_score", ascending=False)
          .head(20)
          .to_string(index=False))

    # ── Update market_potential_grid in DB ────────────────────────────────
    print(f"\nUpdating is_white_space in market_potential_grid...")
    cur = conn.cursor()

    # Reset all first
    cur.execute("UPDATE market_potential_grid SET is_white_space = FALSE")
    conn.commit()

    updated_total = 0
    for _, row in ws_df.iterrows():
        cur.execute("""
            UPDATE market_potential_grid
            SET    is_white_space = TRUE
            WHERE  ST_DWithin(
                       geom::geography,
                       ST_SetSRID(
                           ST_MakePoint(%s, %s),   -- longitude first, latitude second
                           4326
                       )::geography,
                       %s
                   )
        """, (
            float(row["centroid_lon"]),
            float(row["centroid_lat"]),
            int(GRID_UPDATE_RADIUS),
        ))
        updated_total += cur.rowcount

    conn.commit()
    cur.close()
    print(f"  ✓ Marked {updated_total:,} grid cells as is_white_space=TRUE")

conn.close()
print("\n── Step 5b complete ─────────────────────────────────────────────")
print("   Step 5 fully done. Next: Step 6 — FastAPI backend.")