# Distributor Touchpoint & Network Expansion Platform
## Step-by-Step Project Guide — Instructions & Data Scale Reference

---

> **What this document is:** A plain-English walkthrough of every step you need to complete this project from scratch. No code — just what to do, why you're doing it, and exactly what scale of data you're working with at each stage.

---

## Table of Contents
1. [Environment Setup](#step-1-environment-setup)
2. [Synthetic Data Generation](#step-2-synthetic-data-generation)
3. [Spatial Database Setup](#step-3-spatial-database-setup)
4. [Data Ingestion & Cleaning Pipeline](#step-4-data-ingestion--cleaning-pipeline)
5. [Machine Learning & Analytics Engine](#step-5-machine-learning--analytics-engine)
6. [Backend API Development](#step-6-backend-api-development)
7. [Frontend Web Application](#step-7-frontend-web-application)
8. [Role-Based Access Control](#step-8-role-based-access-control-rbac)
9. [Touchpoint Approval Workflow](#step-9-touchpoint-approval-workflow)
10. [Cloud Deployment](#step-10-cloud-deployment)
11. [Testing & QA](#step-11-testing--qa)
12. [Documentation & Presentation](#step-12-documentation--presentation)

---

## Step 1: Environment Setup

**What you are doing:** Installing every tool and library the project depends on, and organizing your project folder so nothing becomes a mess later.

**Why this matters:** A clean environment prevents 80% of "it works on my machine" problems. The folder structure you set up now will be the same structure your entire team (and your evaluators) will navigate.

### Tools to Install

- **Python 3.11+** — for data generation, cleaning, and the ML engine
- **Node.js LTS (v20+)** — for the backend API server
- **PostgreSQL 15+** — the relational database; install with Stack Builder so you can add PostGIS
- **PostGIS extension** — installs on top of PostgreSQL; this is what gives the database the ability to understand maps, coordinates, and geometric shapes
- **Git** — for version control; commit your work after completing each step
- **pgAdmin** — a visual interface to manage your PostgreSQL database; comes bundled with PostgreSQL installer
- **Postman** — for testing your backend APIs manually before connecting the frontend
- **VS Code** — recommended code editor

### Python Libraries to Install

You will install all of these into a virtual environment (an isolated Python workspace so library versions don't conflict):

- **pandas** — data manipulation and CSV handling
- **geopandas** — pandas but for geographic data; handles shapefiles and coordinate operations
- **numpy** — numerical computations
- **scikit-learn** — machine learning algorithms
- **xgboost** — the gradient boosting ML algorithm you will use for revenue prediction
- **shapely** — creating and working with geometric shapes (polygons, points, lines)
- **psycopg2** — connects Python to PostgreSQL
- **sqlalchemy** — higher-level database interaction from Python
- **faker** — generates realistic fake Indian names, addresses, phone numbers, and pin codes
- **geopy** — geocoding (converting addresses to lat/long coordinates)
- **matplotlib & seaborn** — data visualization for your ML analysis notebooks
- **jupyter** — for exploratory data analysis in notebook format
- **fastapi & uvicorn** — alternative backend option if you choose Python over Node.js

### Node.js Libraries to Install (for the backend)

- **express** — the web framework for building REST APIs
- **pg** — connects Node.js to PostgreSQL
- **cors** — allows the React frontend to communicate with the backend
- **dotenv** — loads secret keys from a `.env` file instead of hardcoding them
- **bcryptjs** — hashes user passwords before storing in the database
- **jsonwebtoken** — creates and verifies authentication tokens

### React Libraries to Install (for the frontend)

- **mapbox-gl** — the mapping engine that renders your interactive India map
- **@mapbox/mapbox-gl-draw** — adds tools to draw polygons on the map (for territory management)
- **axios** — makes HTTP requests from React to your backend API
- **react-router-dom** — handles navigation between pages in the React app
- **tailwindcss** — utility-based CSS framework for styling the UI quickly

### Folder Structure to Create

Set up six top-level folders inside your project root:

- `data/` — with subfolders `raw/` (original generated files) and `processed/` (cleaned files ready to load)
- `data-generation/` — all Python scripts that produce synthetic data
- `ml-engine/` — ML training scripts, saved models, and Jupyter notebooks
- `backend/` — the Node.js API server
- `frontend/` — the React web application
- `database/` — SQL schema files and migration scripts
- `docs/` — architecture diagrams, your BRD, and meeting notes

---

## Step 2: Synthetic Data Generation

**What you are doing:** Since there is no real business data available, you will write Python scripts to generate realistic fake data that behaves like real-world Parts & Accessories business data across India.

**Why this matters:** The ML models, the maps, and the approval workflows all depend on data existing. Everything you build in Steps 3–9 is pointless without this data. The data you generate here will be the foundation of your entire demo.

---

### 2.1 Location Data — The Map Pins

You need to generate 6 types of physical locations, distributed across India in a geographically realistic way. Larger cities like Mumbai, Delhi, and Bengaluru should have more touchpoints than smaller cities — this mirrors how real distribution networks are structured.

| Entity Type | What It Represents | Records to Generate |
|---|---|---|
| Mother Warehouse (MW) | Large central stocking hubs | **18** |
| Additional Warehouse (AW) | Secondary regional hubs | **55** |
| Retail Office (RO) | Customer-facing sales offices | **180** |
| Dealer Touchpoints | Authorized parts dealers | **700** |
| Independent Workshops | Unaffiliated garages and mechanics | **4,500** |
| MASS (Manufacturer Authorized Service Stations) | Brand-authorized repair centers | **400** |
| **Total Location Records** | | **~5,853** |

For each record, you need to generate these fields:
- A unique ID (e.g., `DLR-0042`, `MW-0003`)
- Name, city, full address, pin code, state
- Contact person name and phone number
- **Latitude and Longitude** — the most important fields; these place the pin on the map
- An `active` flag (True/False) — 95% should be active

**How to distribute the coordinates:** Use a list of 20 major Indian cities and assign coordinates near each city, with a small random offset so pins don't all stack exactly on the city center. Weight cities by population — Mumbai, Delhi, and Bengaluru should get proportionally more pins than Bhubaneswar or Guwahati.

---

### 2.2 Historical Sales Data — The Revenue History

You need 3–5 years of monthly sales records per dealer. This data trains your market potential ML model.

| Field | Description |
|---|---|
| Dealer ID | Links back to the dealer in your locations data |
| Sale Date | Random date between Jan 2020 and Dec 2024 |
| Parts Category | One of 8 categories (Engine Parts, Brakes, Electrical, etc.) |
| Units Sold | Random integer, typically 10–500 per record |
| Revenue (₹) | Random value between ₹50,000 and ₹15,00,000 per record |

**Scale:** 700 dealers × ~24 records each = approximately **16,800 sales records**

---

### 2.3 Vehicle Parc Grid Data — The Market Intelligence

This is the most important dataset for ML. It maps how many company vehicles exist in each 5×5 km cell across India.

Think of India divided into a massive grid of small squares. For each square, you record:
- The center latitude and longitude of that grid cell
- How many company vehicles are registered in that area
- Average age of those vehicles
- Percentage that are commercial vehicles (trucks, vans) — these consume far more parts

**Scale:** Covering India (approximately 3.3 million km²) at a 5×5 km resolution gives roughly **130,000–150,000 non-empty grid cells** after filtering out ocean and uninhabited areas.

---

### 2.4 User Accounts — For the Login System

Manually create or generate a small set of user accounts for testing:

- **2–3 Org Admin accounts** — full access, no distributor ID assigned
- **10–15 Distributor User accounts** — each linked to one distributor ID, restricted view

---

## Step 3: Spatial Database Setup

**What you are doing:** Creating a PostgreSQL database with the PostGIS extension enabled, then defining the table structure (schema) that will hold all your data.

**Why this matters:** A regular database stores rows and columns. PostGIS adds a special data type called `geometry` that can store points, lines, and polygons — and more importantly, lets you query them spatially. For example: "find all workshops within 15 km of this dealer" or "check if this proposed location falls inside this territory boundary." Without PostGIS, you cannot do any of this.

### Database to Create

Create one database called `distributor_gis`. Enable the PostGIS extension immediately after creation — this is a one-time command.

### Tables to Create

**`locations` table** — stores every physical touchpoint (all 5,853 records)
- Columns: ID, name, type, city, address, pin code, state, contact info, active flag
- Special column: `geom` — a PostGIS geometry column of type POINT that stores the lat/long as a spatial object in the WGS84 coordinate system (the same system GPS uses)
- Add a spatial index on the `geom` column — this makes map queries dramatically faster when you're filtering by map viewport bounds

**`distributor_territories` table** — stores drawn polygon boundaries
- Columns: ID, territory name, distributor ID, locked flag, created/updated timestamps
- Special column: `boundary` — a PostGIS geometry column of type POLYGON
- Add a spatial index here too — overlap checks between polygons are expensive without it

**`market_potential_grid` table** — stores ML model output for every grid cell
- Columns: grid ID, center lat/long, vehicle count, predicted revenue (₹), hotspot score (0–1), is_white_space flag
- Special column: `geom` — point geometry for the grid center

**`users` table** — stores login credentials and roles
- Columns: ID, username, email, hashed password, role (`org_admin` or `distributor_user`), distributor ID (null for admins)
- Never store plain-text passwords — always store the bcrypt hash

**`ro_requests` table** — stores Retail Office expansion requests
- Columns: ID, requested by (user ID), distributor ID, proposed name, proposed coordinates, status (`PENDING` / `APPROVED` / `REJECTED`), conflict flag, admin note, timestamps
- Special column: `geom` — point geometry for the proposed location

### Indexes to Create

Beyond the spatial indexes, also create regular indexes on:
- `locations.type` — you will filter by entity type very frequently
- `distributor_territories.distributor_id` — to quickly fetch a specific distributor's territories
- `ro_requests.status` — admins will frequently query for all PENDING requests

---

## Step 4: Data Ingestion & Cleaning Pipeline

**What you are doing:** Taking the raw CSV files you generated in Step 2, cleaning them through three layers of coordinate validation, and loading them into the PostgreSQL database you set up in Step 3.

**Why this matters:** Raw generated data always has noise — missing values, coordinates that drifted outside city bounds, points that landed in the sea, and inconsistent text formatting. Loading dirty data leads to broken map queries, pins appearing in the ocean, and inaccurate ML models. Coordinate validation is especially critical because a single bad lat/long silently corrupts spatial queries without throwing an obvious error.

### Cleaning Steps to Apply

There are three layers of coordinate validation applied in sequence, from broadest to most precise. A record must pass all three to be loaded into the database.

---

**Layer 1 — National Bounding Box Check (coarsest)**

Check that every latitude is between **6.0°N and 37.6°N**, and every longitude is between **68.0°E and 97.5°E**. These are the rectangular outer bounds of India. Any point outside this box is clearly wrong — drop it immediately. This catches extreme drift errors like a coordinate accidentally written as `(720.5, 77.2)` due to a data entry bug.

*Expected drop rate from synthetic data: less than 0.5% — mostly just extreme outliers.*

---

**Layer 2 — City Radius Check (medium precision)**

This is the most important validation layer. Just because a coordinate passes the India bounding box check does not mean it is actually near the city it was assigned to. When you generated data in Step 2, you added a random offset (jitter) to each city's center coordinate. If the jitter was too large, a record assigned to Mumbai could have drifted into the Arabian Sea, or a record assigned to Delhi could have landed in Himachal Pradesh — both of which are inside India's bounding box but clearly wrong.

**What to do:** For every record in the cleaned data, compute the straight-line distance (in kilometers) between the record's actual coordinates and the known center coordinates of the city it is assigned to. If the distance exceeds the city's allowed radius, the record fails this check.

**Allowed radius thresholds by city tier:**

| City Tier | Examples | Allowed Radius |
|---|---|---|
| Tier 1 Metros | Mumbai, Delhi, Bengaluru, Chennai, Hyderabad, Kolkata | 60 km |
| Tier 1 Large Cities | Pune, Ahmedabad, Surat, Jaipur | 45 km |
| Tier 2 Cities | Nagpur, Indore, Bhopal, Lucknow, Patna | 35 km |
| Tier 3 / Smaller | Coimbatore, Kochi, Chandigarh, Guwahati | 25 km |

The rationale for larger radii for metros: Mumbai's urban area genuinely spans 60+ km (from Virar to Panvel), so a dealer legitimately "in Mumbai" could be far from the city center coordinate. Smaller cities have tighter urban footprints.

**What to do with records that fail:** Do not drop them immediately. Instead, flag them with a column called `coord_validation_status` set to `"CITY_RADIUS_FAIL"`. Then attempt to auto-correct by regenerating the coordinate with a smaller jitter. If the regenerated coordinate passes, update the record and mark it `"CORRECTED"`. If it still fails after 3 retry attempts, mark it `"DROPPED"` and exclude it from the database load.

*Expected fail rate from synthetic data: 2–5% depending on the jitter spread used during generation.*

---

**Layer 3 — State Boundary Polygon Check (most precise)**

Even after the city radius check, a coordinate could technically be within 60 km of Mumbai's center but still fall in the sea (Mumbai is coastal). This layer catches those cases.

**What to do:** Download a free GeoJSON file of India's state boundaries. A reliable source is the **Datameet India Maps repository** on GitHub, which provides district and state boundary shapefiles. Load this shapefile using GeoPandas.

For each record that passed Layers 1 and 2, run a **point-in-polygon check**: does this coordinate fall inside the polygon of the state that this record is assigned to? For example, a Mumbai record must fall inside the Maharashtra polygon.

This check does two things simultaneously:
- It confirms the point is on land (not in the ocean or a neighboring country)
- It confirms the point is in the correct state (a "Hyderabad" record shouldn't be in Karnataka)

**What to do with records that fail:**
- If the point is in a neighboring state (e.g., a Hyderabad record landed in Telangana instead of the expected state), check whether the city actually straddles a state border. Hyderabad is in Telangana, so flag as `"STATE_MISMATCH"` and correct the state field in the record rather than dropping it.
- If the point is in the ocean or outside India entirely, mark as `"OFFSHORE"` and drop it.

*Expected fail rate: less than 1% after Layer 2 already caught most drift errors.*

---

**Layer 4 — Missing Value and Format Checks**

After the three coordinate layers, apply these standard data quality checks:

**Missing value handling:** Drop rows with missing latitude, longitude, or entity type — these three fields are the minimum required for the record to be useful. For other missing fields like contact name or phone, fill with a placeholder (`"Unknown"`) rather than dropping the whole row.

**Text standardization:** Apply title case to city and state names. Trim leading and trailing whitespace. Ensure entity type strings match exactly what the database expects — the system is case-sensitive (e.g., `"Dealer"` not `"dealer"` or `"DEALER"`).

**Duplicate check:** Check for duplicate IDs. If any exist, keep the first occurrence and drop the rest. Also check for near-duplicate coordinates — two records of the same type at almost identical coordinates (within 100 meters of each other) likely represent a data generation error and the second one should be dropped.

---

### Validation Summary Log

After running all cleaning steps, produce a summary log file (`data/processed/validation_log.csv`) that records:
- Total records input
- Records dropped at each layer (with reason)
- Records auto-corrected
- Final records loaded into the database

This log is useful to include in your project documentation as evidence of data quality control.

### City Reference Table Used for Validation

Maintain a master city reference table (`data/raw/city_reference.csv`) with columns: city name, state, center latitude, center longitude, allowed radius (km), and tier. This table is the ground truth for Layer 2 validation and should cover all 20 cities used during data generation. Any city in your location data that does not appear in this reference table should be flagged as `"UNKNOWN_CITY"` and reviewed manually.

### Loading Into the Database

When inserting location records into the database, you must convert the latitude/longitude columns into a PostGIS geometry object using the `ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)` function. Note the order: longitude first, then latitude — this is the correct order for PostGIS and it trips people up constantly.

Load the data in this order:
1. `users` table first (no dependencies)
2. `locations` table second
3. `market_potential_grid` table third (after ML output is ready in Step 5)
4. `distributor_territories` table fourth (drawn through the app, but you can seed a few for demo)
5. `ro_requests` table last (generated through the app workflow)

### Data Volume in the Database After Loading

| Table | Expected Row Count |
|---|---|
| locations | ~5,853 |
| users | ~18 |
| market_potential_grid | ~135,000 |
| distributor_territories | ~20 (seeded for demo) |
| ro_requests | generated during demo |

---

## Step 5: Machine Learning & Analytics Engine

**What you are doing:** Training two predictive models using Python. The first predicts revenue potential for every grid cell in India. The second identifies dense clusters of workshops that have no dealer coverage nearby.

**Why this matters:** These two models are what make this platform more than just a map. They are the "intelligence" layer that tells the business where to expand next — which is the entire point of the system.

---

### Model 1: Market Potential Predictor

**Goal:** For every 5×5 km grid cell across India, output a predicted annual parts revenue in ₹ and a normalized hotspot score between 0 and 1.

**Algorithm:** XGBoost (Extreme Gradient Boosting) — a decision-tree-based ensemble model that is extremely effective on tabular data with mixed numeric features.

**Input Features (what the model learns from):**

| Feature | Why It Matters |
|---|---|
| Vehicle count in the grid cell | More vehicles = more parts demand |
| Average vehicle age | Older vehicles need more replacement parts |
| Commercial vehicle percentage | Trucks and vans consume far more parts than passenger cars |
| Weighted vehicle score | A combined feature: vehicle count × commercial % ÷ average age |

**Target variable:** Potential annual parts revenue in ₹ per grid cell

**Training data scale:** ~135,000 grid cell records, split 80% training / 20% testing

**Expected performance metrics to aim for:**
- R² score above 0.70 (the model explains at least 70% of variance in revenue)
- Mean Absolute Error below ₹20,000 per grid cell

**Output:** A CSV file with predicted revenue and hotspot score for every grid cell, which gets loaded into the `market_potential_grid` table in the database.

---

### Model 2: White-Space / Untapped Pocket Detector

**Goal:** Find geographic clusters of Independent Workshops that have no Dealer within 15 km. These are "white spaces" — areas with proven vehicle maintenance demand but no authorized dealer coverage.

**Algorithm:** DBSCAN (Density-Based Spatial Clustering of Applications with Noise) — a clustering algorithm that finds dense groupings in geographic data without needing you to specify how many clusters there are in advance.

**How it works, step by step:**

1. Feed all 4,500 Independent Workshop coordinates into DBSCAN
2. DBSCAN groups nearby workshops into clusters (minimum 10 workshops within ~5 km to form a cluster)
3. For each cluster, compute its geographic centroid (center point)
4. For each centroid, check the distance to the nearest Dealer touchpoint
5. If the nearest dealer is more than 15 km away → that cluster is flagged as a **white space**
6. Assign each white space an opportunity score based on cluster size (larger cluster = higher score)

**Output scale:** Expect to find approximately **80–150 white-space pockets** across India, concentrated in Tier-2 and Tier-3 cities and rural corridors.

**Output:** A CSV file of white-space centroids with coordinates and opportunity scores, which gets loaded into the database and displayed as a special layer on the map.

---

### Saving the Models

Save both trained models as `.pkl` files using joblib. This means you can load the model later and run predictions on new data without retraining from scratch. Store saved models in `ml-engine/models/`.

---

## Step 6: Backend API Development

**What you are doing:** Building a REST API server that sits between the database and the frontend. The frontend never talks directly to the database — it always goes through the API.

**Why this matters:** The API is where all business logic lives — authentication, permission checks, spatial conflict validation. It protects the database from direct access and ensures business rules are enforced consistently.

### Technology Choice

Use either **Node.js with Express** or **Python with FastAPI**. Both are equally valid. Node.js is faster to set up for REST APIs; FastAPI is a natural choice if your whole team is more comfortable in Python.

### API Endpoints to Build

**Authentication:**
- `POST /api/auth/login` — accepts email + password, returns a JWT token if credentials are valid
- `POST /api/auth/logout` — invalidates the session token

**Locations:**
- `GET /api/locations` — returns location records; supports query parameters to filter by type, city, and map viewport bounds (so the map only fetches what's visible)
- `GET /api/locations/:id` — returns a single location's full details

**Analytics:**
- `GET /api/analytics/hotspots` — returns market potential grid cells, filterable by minimum hotspot score
- `GET /api/analytics/whitespaces` — returns all identified white-space pockets with opportunity scores
- `GET /api/analytics/summary` — returns aggregate counts and total revenue potential by region (for the dashboard KPI cards)

**Territories:**
- `GET /api/territories` — returns all territories (admin) or just the requesting distributor's territory
- `POST /api/territories` — saves a newly drawn polygon; runs a spatial overlap check before saving; returns a conflict error if it intersects any locked territory
- `PATCH /api/territories/:id/lock` — locks a territory so it cannot be edited or overlapped

**Workflow:**
- `POST /api/workflow/request-ro` — distributor submits a new Retail Office request; system validates that the proposed point falls within their own territory before saving
- `GET /api/workflow/requests` — admin fetches all pending RO requests
- `PATCH /api/workflow/requests/:id` — admin approves or rejects a request; if approved, a new record is added to the locations table

### Middleware to Build

**JWT Authentication Middleware:** Applied to every protected route. Reads the Authorization header, verifies the JWT token signature, and attaches the decoded user object (including role and distributor ID) to the request so downstream route handlers can use it.

**RBAC Middleware:** A role-checking function that certain routes call before executing. For example, the `POST /api/territories` route requires `org_admin` role. If a distributor user tries to call it, they get a 403 Forbidden response.

**Error Handling Middleware:** A global error handler that catches unhandled exceptions and returns a clean JSON error message rather than crashing the server or exposing stack traces.

### Environment Variables

Store all secrets in a `.env` file that is never committed to Git:
- Database connection string
- JWT signing secret
- Mapbox API token
- Port number

---

## Step 7: Frontend Web Application

**What you are doing:** Building the React web application that users actually interact with — the map, the dashboards, the territory drawing tools, and the approval forms.

**Why this matters:** This is the face of the entire platform. All the data, ML models, and APIs you've built only become useful when visualized clearly for a business user.

### Pages to Build

**Login Page (`/login`):**
A simple centered form with email and password fields. On successful login, store the JWT token in React state (not localStorage for security) and redirect to the appropriate dashboard based on the user's role.

**Org Admin Dashboard (`/dashboard`):**
The main page for an admin. Contains:
- A full-screen interactive India map (Mapbox) as the primary visual
- A sidebar with layer toggle checkboxes (turn each entity type on/off)
- KPI cards at the top: total touchpoints, total territories locked, pending RO requests, total market potential ₹
- A toggle to switch between "Touchpoint View" (colored pins) and "Heatmap View" (ML hotspot layer)

**Territory Manager (`/territories`):**
Available only to Org Admins. Contains:
- The same map with a polygon drawing toolbar activated
- A list panel on the side showing all existing territories with their lock status
- When the admin finishes drawing a polygon, a modal pops up asking for the territory name and distributor assignment
- If the system detects an overlap with a locked territory, the save button is disabled and a red warning message is shown

**Distributor Dashboard (`/my-territory`):**
The restricted view for distributor users. Shows:
- A map zoomed into and clipped to their assigned territory only
- Their assigned touchpoints within the territory
- ML "Untapped Pockets" highlighted within their zone (white-space layer)
- A prominent "Request New Retail Office" button

**RO Request Form (`/request-ro`):**
A map where the distributor can drop a pin at the proposed location. Below the map, a form captures the proposed name and brief justification. On submit, the system validates the pin is within their territory.

**Admin Approvals Page (`/approvals`):**
A table/card list of all PENDING RO requests. Each card shows: which distributor submitted it, the proposed coordinates shown on a small embedded map, and Approve / Reject buttons with a text field for the admin's note.

### Map Features to Implement

**Clustering:** When zoomed out to the national level, thousands of individual pins would overlap and be unreadable. Use Mapbox's built-in clustering to group nearby points into a single circle showing the count. As the user zooms in, clusters break apart into individual pins.

**Popup on Click:** Clicking any pin opens a small popup showing the entity name, type, city, and contact details.

**Layer Filtering:** A checkbox panel controls which entity types are visible. When a type is unchecked, its pins are hidden from the map without re-fetching data from the API.

**Viewport-based Data Fetching:** As the user pans or zooms the map, the app sends the current map bounds (min/max lat/long) to the API. The API returns only the locations visible in that viewport, preventing the browser from loading all 5,853 points at once.

**Heatmap Toggle:** A toggle button switches the map from pin view to a color-gradient heatmap based on ML hotspot scores. Hot areas (high revenue potential) appear in red/orange; cooler areas appear in blue/green.

**Territory Polygons Layer:** Draw all locked distributor territories as semi-transparent colored polygons on the map. Each polygon should have a visible label with the territory name.

---

## Step 8: Role-Based Access Control (RBAC)

**What you are doing:** Ensuring that Org Admins and Distributor Users see completely different views of the platform, and that neither can access what the other is authorized for.

**Why this matters:** A distributor must never see another distributor's territory data, customer list, or ML insights. An admin must have complete visibility. This isn't just a UI concern — it must be enforced at the API level.

### The Two Roles

**Org Admin:**
- Can see all regions, all distributors' territories, all ML insights nationally
- Can draw, edit, and lock territory boundaries
- Can approve or reject RO expansion requests
- Can see all pending requests from all distributors

**Distributor User:**
- Can only see their own assigned territory boundary on the map
- Can only see their own assigned customers and touchpoints
- Can see ML "Untapped Pockets" but only within their territory
- Can submit new RO requests but cannot approve them
- Cannot see any other distributor's data

### How RBAC is Enforced

**At the API level (the right way):** Every protected API endpoint checks the user's role from the JWT token before returning data. The locations endpoint, for example, automatically appends a `WHERE distributor_id = <user's distributor ID>` filter for distributor users, even if they try to pass different parameters.

**At the UI level (user experience):** The React Router is configured with Protected Route components that check the user's role and redirect unauthorized users to a "403 Forbidden" page if they try to navigate to a route they shouldn't access.

**Login and token flow:**
1. User submits email and password on the login form
2. Backend verifies the password against the stored bcrypt hash
3. If valid, backend creates a JWT token containing: user ID, role, and distributor ID (if applicable)
4. Token is returned to the frontend and stored in React's context/state
5. Every subsequent API request from the frontend includes this token in the `Authorization: Bearer <token>` header
6. The backend's auth middleware verifies and decodes the token on every request

---

## Step 9: Touchpoint Approval Workflow

**What you are doing:** Building the end-to-end digital business process that allows distributors to request new Retail Office locations and allows admins to approve or reject them — replacing what would otherwise be email chains or paper forms.

**Why this matters:** This is one of the highest-value features of the platform. It digitizes a real business process, creates an audit trail, and enforces geographic rules automatically.

### The Full Workflow, Step by Step

**Step 1 — Distributor drops a pin:** On their restricted map view, the distributor clicks to place a pin at the proposed location for the new Retail Office.

**Step 2 — System validates territory ownership:** The moment the pin is dropped, the frontend sends the coordinates to the backend. The backend runs a PostGIS spatial query: "Does this point fall inside a territory assigned to this distributor?" If not, the pin turns red and the submit button stays disabled.

**Step 3 — Distributor fills in the form:** If the pin is valid (inside their territory), the form fields become active. The distributor enters the proposed name, address, and a brief business justification.

**Step 4 — Request is saved as PENDING:** On submission, a record is created in the `ro_requests` table with status `PENDING`. The distributor sees a confirmation: "Your request has been submitted and is under review."

**Step 5 — Admin receives a notification:** The next time an Org Admin logs in (or if you implement real-time notifications via websockets, immediately), they see a badge count on the Approvals menu item.

**Step 6 — Admin reviews the request:** On the Approvals page, the admin sees a map preview of the proposed location alongside the distributor's existing territory and touchpoints. They can visually assess whether the new location makes geographic sense.

**Step 7 — Admin approves or rejects:** If approved, the system automatically creates a new entry in the `locations` table with type "Retail Office" and status active. The `ro_requests` record is updated to status `APPROVED`. If rejected, the admin must enter a rejection reason. The `ro_requests` record is updated to status `REJECTED` with the admin's note.

**Step 8 — Distributor sees the outcome:** On their next dashboard load, the new RO appears on their map (if approved), or they see the rejection reason in a notification.

### Conflict Prevention Built Into the Workflow

The system should also check — at the time of approval — whether the proposed RO location is already within 5 km of another existing touchpoint of the same type. If it is, the system flags this as a potential cannibalization risk and shows the admin a warning before they approve.

---

## Step 10: Cloud Deployment

**What you are doing:** Moving the application from your local machine to a cloud server so it can be accessed from any browser.

**Why this matters:** For your internship demo and presentation, having a live URL is far more impressive than running `localhost` on your laptop.

### Recommended Architecture (AWS Free Tier)

AWS provides a free tier that covers everything you need for 12 months:

| Component | AWS Service | Notes |
|---|---|---|
| React Frontend | S3 + CloudFront | Host the built React files as a static website |
| Backend API | EC2 t2.micro | 1 free instance, run Node.js here |
| PostgreSQL + PostGIS | RDS db.t3.micro | Managed database, automatic backups |
| File Storage (CSVs, model files) | S3 bucket | Free up to 5 GB |

### Containerization with Docker

Before deploying to the cloud, containerize the application using Docker. This means packaging the backend and its dependencies into a Docker image that runs identically on your laptop, on EC2, or on any other server.

Create a `docker-compose.yml` file in the project root that defines three services: the database (using the official postgis/postgis Docker image), the backend API, and the frontend. Running `docker-compose up` starts the entire stack locally in one command — extremely useful for demos.

### Deployment Steps in Order

1. Build the React app for production (`npm run build`) — this creates an optimized static bundle
2. Upload the built frontend to an S3 bucket configured for static website hosting
3. Set up a CloudFront distribution pointing to the S3 bucket (for HTTPS and CDN caching)
4. Launch an EC2 instance, install Node.js, copy the backend code, set environment variables
5. Launch an RDS PostgreSQL instance, enable PostGIS, run your schema SQL
6. Load all data from your CSVs into the RDS database
7. Update the backend `.env` to point to the RDS endpoint instead of `localhost`
8. Update the React app's API base URL to point to the EC2 server's public IP

---

## Step 11: Testing & QA

**What you are doing:** Systematically verifying that every part of the system works correctly before your final presentation.

### Backend API Testing (Using Postman)

Test every endpoint manually in Postman before writing automated tests. For each endpoint, verify:
- Does it return 200 with correct data when called with valid credentials and parameters?
- Does it return 401 when called without a token?
- Does it return 403 when a distributor user calls an admin-only endpoint?
- Does it return the correct error message and status code for invalid inputs?

**Specifically test the spatial logic:**
- Submit a territory polygon that overlaps an existing locked territory — confirm the API returns a conflict error and does not save the polygon
- Submit an RO request with coordinates outside the distributor's territory — confirm the API rejects it
- Submit an RO request with valid coordinates — confirm it saves with status PENDING

### ML Model Validation Checklist

- [ ] Market Potential model R² score is above 0.70 on the test set
- [ ] Predicted revenues are all positive numbers (no negative values)
- [ ] Hotspot scores are all between 0 and 1
- [ ] White-space clusters are geographically sensible — they should appear in areas with high workshop density but low dealer density (typically Tier-2/3 cities and semi-rural corridors)
- [ ] White-space centroid coordinates are all within India's geographic bounds

### Frontend Testing Checklist

- [ ] Map loads without errors and centers on India at the correct zoom level
- [ ] All 6 entity type layers toggle on and off correctly
- [ ] Clicking a pin opens the correct popup with that pin's details
- [ ] Zooming in breaks clusters into individual pins
- [ ] Heatmap toggle switches the view correctly
- [ ] Territory polygons are visible and correctly labeled
- [ ] Admin can draw a polygon and see a conflict warning when it overlaps an existing territory
- [ ] Distributor dashboard shows only their territory (not the entire map)
- [ ] RO request form validates that the pin is inside the territory before enabling submission

### RBAC Testing Checklist

- [ ] Logging in as Org Admin shows the full Pan-India dashboard
- [ ] Logging in as a Distributor shows only the restricted territory view
- [ ] Manually calling an admin-only API endpoint with a distributor's token returns 403
- [ ] Distributor cannot navigate to `/territories` or `/approvals` in the browser

---

## Step 12: Documentation & Presentation

**What you are doing:** Writing the project documentation and preparing for your final internship presentation.

### What to Include in the Technical Documentation

**Data Dictionary:** A table for every database table describing each column's name, data type, and purpose. Especially document the geometry columns — explain what coordinate system (WGS84 / EPSG:4326) is used and why.

**Architecture Diagram:** Recreate the 4-layer architecture diagram from the BRD (Data Sources → Spatial Backend → Analytics/ML Engine → API Gateway → Web Application) with your specific technology choices filled in.

**API Reference:** For each endpoint, document the HTTP method, URL, required headers, request body (if any), and a sample successful response.

**ML Model Cards:** One page per model explaining: what the model predicts, what data it was trained on, what algorithm was used, and the performance metrics achieved on the test set.

**Data Generation Methodology:** Explain how synthetic data was produced, the assumptions made (city weighting, vehicle density distributions), and how a real deployment would replace this with live data.

### What to Include in the Presentation Slides

1. **Problem Statement** — What gaps exist in the current manual process?
2. **Solution Overview** — The architecture diagram with one-line descriptions of each layer
3. **Data at a Glance** — A summary table of data volumes (5,853 locations, 16,800 sales records, 135,000 grid cells)
4. **ML Insights** — Show the hotspot heatmap and call out 3–4 specific high-opportunity zones
5. **Live Demo** — Walk through the 8-step demo script below
6. **RBAC in Action** — Show the same data from Admin vs. Distributor perspective side by side
7. **What's Next** — If this were a production system, what real data sources would replace the synthetic data? (VAHAN database for vehicle parc, DMS for sales history, Google Maps Platform for geocoding)

### 8-Step Demo Script

Walk through these scenarios in this exact order for a clean, story-driven demo:

1. **Login as Org Admin** → The Pan-India dashboard loads showing 5,800+ colored dots across the country
2. **Toggle Layers** → Uncheck "Independent Workshop" to de-clutter the map; show just Dealers and Warehouses
3. **Switch to Heatmap View** → Toggle the ML hotspot layer; point out 2–3 specific red zones (high opportunity areas with no current coverage)
4. **Draw a Territory** → Use the polygon drawing tool to draw a boundary around a city; attempt to draw one that overlaps an existing territory and show the system blocking it with a warning
5. **Lock the Territory** → Lock a correctly drawn territory and show it turns solid on the map
6. **Login as Distributor** → Show the completely different, restricted view — only their territory visible
7. **Submit an RO Request** → Drop a pin inside their territory, fill in the form, submit; confirm the PENDING status appears
8. **Back to Admin — Approve the Request** → Show the pending request notification, open it, view the proposed pin on the map preview, approve it; refresh the map to show the new touchpoint appearing

---

## Full Data Scale Summary

| Dataset | Records | File Size (approx) |
|---|---|---|
| Location master data | 5,853 rows | ~1.5 MB |
| Historical sales data | ~16,800 rows | ~2 MB |
| Vehicle parc grid data | ~135,000 rows | ~18 MB |
| Users (login accounts) | ~18 rows | negligible |
| Market potential predictions | ~135,000 rows | ~22 MB |
| White-space pockets identified | ~100–150 rows | negligible |
| Territory polygons (seeded) | ~20 polygons | negligible |
| **Total data loaded in database** | **~290,000 rows** | **~45 MB** |

This is a realistic prototype-scale dataset — large enough that performance optimizations (spatial indexes, viewport-based fetching, map clustering) are visibly necessary and demonstrably effective, but small enough to run comfortably on free-tier cloud infrastructure.

---

*Work through each step in sequence. Every step produces outputs that the next step depends on. The logical order is: generate data → store it → enrich it with ML → serve it via API → display it in the UI.*
