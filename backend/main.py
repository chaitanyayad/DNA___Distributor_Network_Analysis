from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import create_pool, close_pool
from backend.routers import auth, locations, analytics, territories, workflow


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler — runs setup before the app starts accepting
    requests and teardown when the app shuts down.

    create_pool() opens the asyncpg connection pool to PostgreSQL.
    close_pool() drains it cleanly on shutdown.
    """
    await create_pool()
    yield
    await close_pool()


app = FastAPI(
    title="Distributor Touchpoint & Network Expansion Platform",
    description=(
        "Geospatial API for Maruti Suzuki's Parts & Accessories distribution network. "
        "Provides location data, ML-powered market analytics, territory management, "
        "and an RO expansion approval workflow."
    ),
    version="1.0.0",
    lifespan=lifespan,
    # Swagger UI available at /docs
    # ReDoc available at /redoc
)

# ---------------------------------------------------------------------------
# CORS — allows the React frontend (running on localhost:5173 in development
# or the CloudFront URL in production) to call this API.
# In production, replace "*" with your actual frontend domain.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server (React)
        "http://localhost:3000",   # CRA dev server (if used)
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(locations.router)
app.include_router(analytics.router)
app.include_router(territories.router)
app.include_router(workflow.router)


@app.get("/", tags=["Health"])
async def root():
    """Health check — confirms the API is running."""
    return {
        "status": "running",
        "docs": "/docs",
        "message": "Distributor Touchpoint Platform API v1.0",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Lightweight health check for load balancers and uptime monitors."""
    return {"status": "healthy"}