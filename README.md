<br/>

![Under Construction](https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&pause=1000&color=F7B731&center=true&vCenter=true&width=600&lines=🚧+Under+Construction+🚧;Coming+Soon...;Something+awesome+is+brewing+☕;Stay+tuned!+🔥)

<br/>

---

## What This Is

Managing a parts distribution network across India — hundreds of dealers, warehouses, retail offices, and thousands of independent workshops — cannot be done effectively with spreadsheets and email chains. This platform replaces that with a single, map-first interface where every touchpoint is visible, every territory boundary is enforced, and every expansion decision is backed by machine learning.

---

## Core Features

| Feature | Description |
|---|---|
| **Interactive India Map** | 5,800+ distributor touchpoints rendered on a live Mapbox map, filterable by entity type |
| **Territory Demarcation** | Admins draw and lock distributor boundaries as polygons; the system blocks any overlapping territory at save time |
| **Market Potential Heatmap** | XGBoost model predicts annual parts revenue potential for every 5×5 km grid cell across India |
| **White-Space Detection** | DBSCAN clustering identifies dense workshop pockets with no dealer coverage within 15 km — the highest-priority expansion targets |
| **RO Approval Workflow** | Distributors request new Retail Office locations via the map; the system validates territory ownership before routing to admin for approval |
| **Role-Based Access** | Org Admins see the full national picture; Distributor Users see only their assigned territory and ML insights within it |

---

## Tech Stack

```
Frontend       React.js + Tailwind CSS + Mapbox GL JS
Backend        Node.js (Express) REST API
Database       PostgreSQL + PostGIS
ML Engine      Python — XGBoost, DBSCAN, GeoPandas, Scikit-learn
Auth           JWT-based RBAC (two roles: org_admin, distributor_user)
Cloud          AWS (S3 + EC2 + RDS) / Docker Compose for local dev
```

---

## Data at a Glance

This project uses synthetic data generated to mirror real-world Parts & Accessories distribution patterns across India.

| Dataset | Records |
|---|---|
| Location master (dealers, warehouses, workshops, MASS, ROs) | ~5,853 |
| Historical sales records (2020–2024) | ~16,800 |
| Vehicle parc grid cells (5×5 km, covering India) | ~135,000 |
| ML market potential predictions | ~135,000 |
| White-space opportunity pockets identified | ~100–150 |
| **Total rows in database** | **~290,000** |

All coordinates are validated through a 3-layer pipeline: national bounding box → city radius check (tiered by city size) → state boundary polygon check using India GeoJSON shapefiles.

---

## Project Structure

```
distributor-gis-platform/
├── data/
│   ├── raw/                  # Generated CSVs (locations, sales, vehicle parc)
│   └── processed/            # Cleaned, validated, ML-enriched data
├── data-generation/          # Python scripts to produce all synthetic datasets
├── ml-engine/
│   ├── models/               # Saved XGBoost and DBSCAN model files
│   └── notebooks/            # Exploratory analysis notebooks
├── backend/                  # Node.js Express API
│   ├── routes/               # locations, territories, analytics, auth, workflow
│   └── middleware/           # JWT verification, RBAC enforcement
├── frontend/                 # React web application
│   └── src/
│       ├── components/       # MapView, FilterPanel, TerritoryDrawer, etc.
│       └── pages/            # Dashboard, Territories, Approvals, Login
├── database/                 # SQL schema and seed files
└── docs/                     # Architecture diagrams, BRD, data dictionary
```

---

## How It Works — Architecture Overview

```
[ Data Sources ]
  Touchpoint Data · Customer Data · Sales History · Vehicle Parc Grid
          │
          ▼
[ Spatial Database ]
  PostgreSQL + PostGIS — stores points, polygons, spatial indexes
          │
          ▼
[ ML & Analytics Engine ]
  Market Potential Model (XGBoost) · White-Space Clustering (DBSCAN)
          │
          ▼
[ REST API ]
  Node.js / Express — auth, RBAC, spatial conflict checks, workflow logic
          │
          ▼
[ Web Application ]
  React + Mapbox — interactive map, territory tools, dashboards, approvals
```

---

## Key Business Logic

**Territory conflict prevention** — when an admin saves a drawn polygon, the backend runs a PostGIS `ST_Intersects` check against all existing locked territories. If any overlap is detected, the save is rejected with a conflict error identifying the overlapping territory by name. No two distributors can ever hold overlapping locked territories.

**RO request validation** — when a distributor submits a new Retail Office request, the backend runs a PostGIS `ST_Within` check to confirm the proposed coordinates fall inside that distributor's assigned territory before the request is even saved. Requests outside territory bounds are rejected before reaching the admin queue.

**White-space scoring** — each untapped pocket is assigned an opportunity score (0–1) based on the size of the workshop cluster relative to the largest cluster found. Larger clusters with no nearby dealer coverage rank highest and are surfaced first on the admin heatmap.

---

## Roles

| Role | Access |
|---|---|
| `org_admin` | Full national view · Draw/lock territories · Approve/reject RO requests · All ML insights |
| `distributor_user` | Own territory only · Own customers only · ML insights scoped to their zone · Submit RO requests |

---

## Local Setup

**Prerequisites:** Node.js 20+, Python 3.11+, PostgreSQL 15+ with PostGIS, Docker (optional)

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/distributor-gis-platform.git
cd distributor-gis-platform

# 2. Set up Python environment and generate data
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python data-generation/generate_locations.py
python data-generation/generate_sales.py
python data-generation/generate_vehicle_parc.py

# 3. Clean and validate data
python data-generation/clean_data.py

# 4. Set up the database
psql -U postgres -c "CREATE DATABASE distributor_gis;"
psql -U postgres -d distributor_gis -c "CREATE EXTENSION postgis;"
psql -U postgres -d distributor_gis -f database/schema.sql
python database/load_data.py

# 5. Train ML models
python ml-engine/train_market_potential.py
python ml-engine/whitespace_analysis.py

# 6. Start the backend
cd backend && cp .env.example .env   # fill in your DB credentials + JWT secret
npm install && npm run dev

# 7. Start the frontend
cd frontend && npm install
# Add your Mapbox token to .env
npm start
```

Or, using Docker:
```bash
docker-compose up --build
```

---

## Environment Variables

**Backend `.env`:**
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=distributor_gis
DB_USER=postgres
DB_PASSWORD=your_password
JWT_SECRET=your_jwt_secret
PORT=5000
```

**Frontend `.env`:**
```
REACT_APP_MAPBOX_TOKEN=your_mapbox_token
REACT_APP_API_BASE_URL=http://localhost:5000
```

---

## Internship Context

This project was built as part of an internship with the Parts & Accessories department. All data is synthetically generated to simulate real distribution network patterns across India. The architecture is designed to be production-ready — replacing synthetic data sources with live feeds from a DMS (Dealer Management System) and the VAHAN vehicle registration database would require no structural changes to the platform.

---



