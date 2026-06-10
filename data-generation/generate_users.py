import pandas as pd
import os

users = [
    # Org admins
    {"id": "USR-001", "username": "admin_priya",  "email": "priya.admin@company.com",
     "password_plain": "Admin@123", "role": "org_admin", "distributor_id": None},
    {"id": "USR-002", "username": "admin_rahul",  "email": "rahul.admin@company.com",
     "password_plain": "Admin@456", "role": "org_admin", "distributor_id": None},
    {"id": "USR-003", "username": "admin_sneha",  "email": "sneha.admin@company.com",
     "password_plain": "Admin@789", "role": "org_admin", "distributor_id": None},
]

# 15 distributor users — one per territory (expanded from 12 to match 25-city scale)
dist_users = [
    ("Vikram",  "vikram"),  ("Ananya",  "ananya"),  ("Suresh", "suresh"),
    ("Meera",   "meera"),   ("Rajan",   "rajan"),   ("Priti",  "priti"),
    ("Arjun",   "arjun"),   ("Kavya",   "kavya"),   ("Mohan",  "mohan"),
    ("Divya",   "divya"),   ("Kiran",   "kiran"),   ("Aditya", "aditya"),
    ("Neha",    "neha"),    ("Sameer",  "sameer"),  ("Pooja",  "pooja"),
]

for i, (full, uname) in enumerate(dist_users, 4):
    dist_id = f"DIST-{str(i-3).zfill(3)}"
    users.append({
        "id":             f"USR-{str(i).zfill(3)}",
        "username":       f"dist_{uname}",
        "email":          f"{uname}@distributor.com",
        "password_plain": f"Dist@{str(i).zfill(3)}",
        "role":           "distributor_user",
        "distributor_id": dist_id,
    })

os.makedirs("../data/raw", exist_ok=True)
df = pd.DataFrame(users)
df.to_csv("../data/raw/users.csv", index=False)
print(f"Generated {len(df)} user accounts → ../data/raw/users.csv")
print("  Org admins : 3")
print(f"  Distributors: {len(df)-3}")
print("WARNING: plain-text passwords — bcrypt hash these in Step 4 before DB insert.")