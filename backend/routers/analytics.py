from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
import asyncpg

from backend.models.location import MarketGridCell, WhiteSpaceResponse
from backend.models.workflow import AnalyticsSummary
from backend.models.user import CurrentUser
from backend.dependencies.auth import get_current_user, require_role
from backend.database import get_db

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/hotspots", response_model=list[MarketGridCell])
async def get_hotspots(
    min_score: float = Query(0.5, ge=0.0, le=1.0, description="Minimum hotspot score (0–1)"),
    limit: int = Query(2000, ge=1, le=10000),
    # Viewport bounds for map-based fetching
    bounds: Optional[str] = Query(None, description="minLon,minLat,maxLon,maxLat"),
    current_user: CurrentUser = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db),
):
    """
    Return market potential grid cells above a hotspot score threshold.
    Used to render the ML heatmap layer on the map.

    Distributor users only see cells within their territory.
    Default min_score=0.5 filters out the bottom half — returns ~65,000 cells
    instead of all 414,000 which would be too heavy for the browser.
    """
    conditions = [
        "hotspot_score >= $1",
        "hotspot_score IS NOT NULL",
    ]
    params: list = [min_score]
    param_idx = 2

    if bounds:
        try:
            min_lon, min_lat, max_lon, max_lat = [float(x) for x in bounds.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="bounds must be in format 'minLon,minLat,maxLon,maxLat'",
            )
        conditions.append(
            f"geom && ST_MakeEnvelope(${param_idx}, ${param_idx+1}, "
            f"${param_idx+2}, ${param_idx+3}, 4326)"
        )
        params.extend([min_lon, min_lat, max_lon, max_lat])
        param_idx += 4

    # RBAC: distributor sees only their territory's grid cells
    if current_user.role == "distributor_user" and current_user.distributor_id:
        conditions.append(
            f"""
            ST_Within(
                geom,
                (SELECT boundary FROM distributor_territories
                 WHERE distributor_id = ${param_idx} AND locked = TRUE LIMIT 1)
            )
            """
        )
        params.append(current_user.distributor_id)
        param_idx += 1

    where_clause = "WHERE " + " AND ".join(conditions)

    rows = await db.fetch(
        f"""
        SELECT
            grid_id,
            ST_Y(geom) AS latitude,
            ST_X(geom) AS longitude,
            vehicle_count,
            predicted_revenue_inr,
            hotspot_score,
            is_white_space
        FROM market_potential_grid
        {where_clause}
        ORDER BY hotspot_score DESC
        LIMIT ${param_idx}
        """,
        *params, limit,
    )

    return [
        MarketGridCell(
            grid_id=r["grid_id"],
            latitude=r["latitude"],
            longitude=r["longitude"],
            vehicle_count=r["vehicle_count"],
            predicted_revenue_inr=r["predicted_revenue_inr"],
            hotspot_score=r["hotspot_score"],
            is_white_space=r["is_white_space"] or False,
        )
        for r in rows
    ]


@router.get("/whitespaces", response_model=list[WhiteSpaceResponse])
async def get_whitespaces(
    current_user: CurrentUser = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db),
):
    """
    Return all grid cells flagged as white-space pockets by the DBSCAN model.
    These are clusters of workshops with no dealer within 15 km — untapped opportunities.
    """
    conditions = ["is_white_space = TRUE"]
    params: list = []
    param_idx = 1

    # Distributor users only see white spaces inside their territory
    if current_user.role == "distributor_user" and current_user.distributor_id:
        conditions.append(
            f"""
            ST_Within(
                geom,
                (SELECT boundary FROM distributor_territories
                 WHERE distributor_id = ${param_idx} AND locked = TRUE LIMIT 1)
            )
            """
        )
        params.append(current_user.distributor_id)
        param_idx += 1

    where_clause = "WHERE " + " AND ".join(conditions)

    rows = await db.fetch(
        f"""
        SELECT
            grid_id,
            ST_Y(geom) AS latitude,
            ST_X(geom) AS longitude,
            vehicle_count,
            hotspot_score
        FROM market_potential_grid
        {where_clause}
        ORDER BY hotspot_score DESC NULLS LAST
        """,
        *params,
    )

    return [
        WhiteSpaceResponse(
            grid_id=r["grid_id"],
            latitude=r["latitude"],
            longitude=r["longitude"],
            vehicle_count=r["vehicle_count"],
            hotspot_score=r["hotspot_score"],
        )
        for r in rows
    ]


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    current_user: CurrentUser = Depends(require_role("org_admin")),
    db: asyncpg.Connection = Depends(get_db),
):
    """
    Return aggregate KPI figures for the admin dashboard cards.
    Admin-only endpoint.
    """
    total_locations = await db.fetchval("SELECT COUNT(*) FROM locations")
    active_locations = await db.fetchval("SELECT COUNT(*) FROM locations WHERE active = TRUE")
    total_territories = await db.fetchval("SELECT COUNT(*) FROM distributor_territories")
    locked_territories = await db.fetchval(
        "SELECT COUNT(*) FROM distributor_territories WHERE locked = TRUE"
    )
    pending_ro = await db.fetchval(
        "SELECT COUNT(*) FROM ro_requests WHERE status = 'PENDING'"
    )
    total_revenue = await db.fetchval(
        "SELECT COALESCE(SUM(predicted_revenue_inr), 0) FROM market_potential_grid"
    )

    # Breakdown of locations by type
    type_rows = await db.fetch(
        "SELECT type, COUNT(*) as cnt FROM locations GROUP BY type ORDER BY type"
    )
    locations_by_type = {r["type"]: r["cnt"] for r in type_rows}

    return AnalyticsSummary(
        total_locations=total_locations,
        active_locations=active_locations,
        total_territories=total_territories,
        locked_territories=locked_territories,
        pending_ro_requests=pending_ro,
        total_predicted_revenue_inr=float(total_revenue),
        locations_by_type=locations_by_type,
    )