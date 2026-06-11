

import pandas as pd
from passlib.context import CryptContext
from pathlib import Path
import random

random.seed(42)

# bcrypt context — requires bcrypt==4.0.1 with passlib==1.7.4
# pip install bcrypt==4.0.1 passlib==1.7.4
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


users = []

# ── Org Admins (3) ────────────────────────────────────────────────────────────
# No distributor_id — they see everything
admin_accounts = [
    ("admin_rahul",   "rahul.sharma@marutisuzuki.com",   "AdminPass@123"),
    ("admin_priya",   "priya.verma@marutisuzuki.com",    "AdminPass@456"),
    ("admin_suresh",  "suresh.nair@marutisuzuki.com",    "AdminPass@789"),
]
for i, (username, email, password) in enumerate(admin_accounts, 1):
    users.append({
        "id":              f"USR-ADM-{str(i).zfill(3)}",
        "username":        username,
        "email":           email,
        "hashed_password": hash_password(password),
        "role":            "org_admin",
        "distributor_id":  None,   # admins have no distributor assignment
    })

# ── Distributor Users (15) ────────────────────────────────────────────────────
# Each linked to one Dealer ID — they see only their territory
distributor_accounts = [
    ("dist_mumbai_1",   "dist.mumbai1@partner.com",   "DistPass@001", "DLR-0001"),
    ("dist_delhi_1",    "dist.delhi1@partner.com",    "DistPass@002", "DLR-0002"),
    ("dist_bengaluru",  "dist.bengaluru@partner.com", "DistPass@003", "DLR-0003"),
    ("dist_chennai",    "dist.chennai@partner.com",   "DistPass@004", "DLR-0004"),
    ("dist_hyderabad",  "dist.hyderabad@partner.com", "DistPass@005", "DLR-0005"),
    ("dist_kolkata",    "dist.kolkata@partner.com",   "DistPass@006", "DLR-0006"),
    ("dist_pune",       "dist.pune@partner.com",      "DistPass@007", "DLR-0007"),
    ("dist_ahmedabad",  "dist.ahmedabad@partner.com", "DistPass@008", "DLR-0008"),
    ("dist_jaipur",     "dist.jaipur@partner.com",    "DistPass@009", "DLR-0009"),
    ("dist_lucknow",    "dist.lucknow@partner.com",   "DistPass@010", "DLR-0010"),
    ("dist_nagpur",     "dist.nagpur@partner.com",    "DistPass@011", "DLR-0011"),
    ("dist_indore",     "dist.indore@partner.com",    "DistPass@012", "DLR-0012"),
    ("dist_patna",      "dist.patna@partner.com",     "DistPass@013", "DLR-0013"),
    ("dist_kochi",      "dist.kochi@partner.com",     "DistPass@014", "DLR-0014"),
    ("dist_guwahati",   "dist.guwahati@partner.com",  "DistPass@015", "DLR-0015"),
]
for i, (username, email, password, dist_id) in enumerate(distributor_accounts, 1):
    users.append({
        "id":              f"USR-DST-{str(i).zfill(3)}",
        "username":        username,
        "email":           email,
        "hashed_password": hash_password(password),
        "role":            "distributor_user",
        "distributor_id":  dist_id,
    })

df = pd.DataFrame(users)

out_path = Path(__file__).parent.parent / "data" / "raw" / "users.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(out_path, index=False)

print(f"Generated {len(df)} users ({len(admin_accounts)} admins, {len(distributor_accounts)} distributors)")
print(f"Saved → {out_path}")
print("\nLogin credentials for testing:")
print("  Admins    : password = AdminPass@123 / @456 / @789")
print("  Distributors: password = DistPass@001 through DistPass@015")
