import pandas as pd
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
import os

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / "backend/.env")

DB_URL = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")

# Load dropped IDs
df      = pd.read_csv(ROOT / "data/raw/locations.csv")
clean   = pd.read_csv(ROOT / "data/processed/locations_clean.csv")
dropped = set(df["id"]) - set(clean["id"])

print(f"Records to remove from DB: {len(dropped)}")

conn = psycopg2.connect(DB_URL)
cur  = conn.cursor()

cur.execute(
    "DELETE FROM locations WHERE id = ANY(%s)",
    (list(dropped),)
)
conn.commit()

print(f"Deleted {cur.rowcount} records from locations table")

cur.execute("SELECT COUNT(*) FROM locations")
print(f"Locations table now has: {cur.fetchone()[0]:,} rows")

cur.close()
conn.close()