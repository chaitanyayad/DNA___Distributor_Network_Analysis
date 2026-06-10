import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv("../backend/.env")

DB_URL = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_conn():
    return psycopg2.connect(DB_URL)

def load_users():
    df   = pd.read_csv("../data/raw/users.csv")
    conn = get_conn()
    cur  = conn.cursor()
    rows = []
    for _, row in df.iterrows():
        rows.append((
            row["id"],
            row["username"],
            row["email"],
            pwd_context.hash(row["password_plain"]),
            row["role"],
            None if pd.isna(row["distributor_id"]) else row["distributor_id"],
        ))
    execute_values(cur,
        """INSERT INTO users (id, username, email, hashed_password, role, distributor_id)
           VALUES %s ON CONFLICT (id) DO NOTHING""",
        rows
    )
    conn.commit()
    cur.close(); conn.close()
    print(f"Loaded {len(rows)} users")

def load_locations():
    df   = pd.read_csv("../data/raw/locations.csv")
    conn = get_conn()
    cur  = conn.cursor()
    rows = []
    for _, row in df.iterrows():
        rows.append((
            row["id"],
            row["name"],
            row["type"],
            row["city"],
            row["state"],
            row["address"],
            str(row["pin_code"]),
            row["contact_person"],
            row["phone"],
            bool(row["active"]),
            float(row["longitude"]),
            float(row["latitude"]),
        ))
    execute_values(cur,
        """INSERT INTO locations
               (id, name, type, city, state, address, pin_code,
                contact_person, phone, active, geom)
           VALUES %s ON CONFLICT (id) DO NOTHING""",
        rows,
        template="""(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                     ST_SetSRID(ST_MakePoint(%s, %s), 4326))"""
    )
    conn.commit()
    cur.close(); conn.close()
    print(f"Loaded {len(rows)} locations")

def load_grid():
    df         = pd.read_csv("../data/raw/vehicle_grid.csv")
    conn       = get_conn()
    cur        = conn.cursor()
    chunk_size = 10_000
    total      = 0
    for start in range(0, len(df), chunk_size):
        chunk = df.iloc[start:start + chunk_size]
        rows  = []
        for _, row in chunk.iterrows():
            rows.append((
                row["grid_id"],
                float(row["center_lat"]),
                float(row["center_lon"]),
                int(row["vehicle_count"]),
                float(row["avg_vehicle_age"]),
                float(row["commercial_pct"]),
                float(row["weighted_vehicle_score"]),
                float(row["center_lon"]),
                float(row["center_lat"]),
            ))
        execute_values(cur,
            """INSERT INTO market_potential_grid
                   (grid_id, center_lat, center_lon, vehicle_count,
                    avg_vehicle_age, commercial_pct, weighted_vehicle_score, geom)
               VALUES %s ON CONFLICT (grid_id) DO NOTHING""",
            rows,
            template="""(%s, %s, %s, %s, %s, %s, %s,
                         ST_SetSRID(ST_MakePoint(%s, %s), 4326))"""
        )
        conn.commit()
        total += len(rows)
        print(f"  Grid: loaded {total:,} / {len(df):,} rows...")

    cur.close(); conn.close()
    print(f"Loaded {total:,} grid cells")

if __name__ == "__main__":
    print("Loading users...")
    load_users()
    print("Loading locations...")
    load_locations()
    print("Loading vehicle grid...")
    load_grid()
    print("\nAll data loaded successfully.")