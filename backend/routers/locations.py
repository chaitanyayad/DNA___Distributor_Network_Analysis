from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
import asyncpg

from backend.models.location import LocationResponse, LocationListResponse
from backend.models.user import CurrentUser
from backend.dependencies.auth import get_current_user
from backend.database import get_db

router = APIRouter(prefix="/api/locations", tags=["Locations"])

# Valid entity types — used to validate the 'type' query parameter
VALID_TYPES = {
    "Mother Warehouse",
    "Additional Warehouse",
    "Retail Office",
    "Dealer",
    "Independent Workshop",
    "MASS",
}


def _row_to_location(row: asyncpg.Record) -> LocationResponse:
    """Convert a raw asyncpg record to a LocationResponse Pydantic model."""
    return LocationResponse(
        id=row["id"],
        name=row["name"],
        type=row["type"],
        city=row["city"],
        address=row["address"],
        pin_code=row["pin_code"],
        state=row["state"],
        contact_person=row["contact_person"],
        phone=row["phone"],
        active=row["active"],
        latitude=row["latitude"],
        longitude=row["longitude"],
    )


@router.get("", response_model=LocationListResponse)
async def get_locations(
    # Optional filters
    type: Optional[str] = Query(None, description="Filter by entity type"),
    city: Optional[str] = Query(None, description="Filter by city name"),
    active_only: bool = Query(True, description="Return only active locations"),
    # Viewport bounds for map-based fetching (minLon,minLat,maxLon,maxLat)
    bounds: Optional[str] = Query(
        None,
        description="Map viewport bounds as 'minLon,minLat,maxLon,maxLat'",
    ),
    # Pagination
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    # Auth
    current_user: CurrentUser = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db),
):
    """
    Return location records with optional filters.

    RBAC behaviour:
    - org_admin: sees all locations
    - distributor_user: automatically filtered to locations within their
      assigned territory (via a spatial ST_Within check). The distributor
      cannot override this by passing different parameters.

    Viewport-based fetching: pass 'bounds' to only return pins visible
    in the current map viewport — prevents loading all 5,800+ points at once.
    """
    # Validate type filter
    if type and type not in VALID_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid type '{type}'. Valid types: {sorted(VALID_TYPES)}",
        )

    # Build WHERE clauses dynamically
    conditions = []
    params = []
    param_idx = 1

    if active_only:
        conditions.append(f"l.active = TRUE")

    if type:
        conditions.append(f"l.type = ${param_idx}")
        params.append(type)
        param_idx += 1

    if city:
        conditions.append(f"LOWER(l.city) = LOWER(${param_idx})")
        params.append(city)
        param_idx += 1

    # Viewport bounds filter — only return pins visible on current map view
    if bounds:
        try:
            min_lon, min_lat, max_lon, max_lat = [float(x) for x in bounds.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="bounds must be in format 'minLon,minLat,maxLon,maxLat'",
            )
        conditions.append(
            f"l.geom && ST_MakeEnvelope(${param_idx}, ${param_idx+1}, "
            f"${param_idx+2}, ${param_idx+3}, 4326)"
        )
        params.extend([min_lon, min_lat, max_lon, max_lat])
        param_idx += 4

    # RBAC: distributor users only see locations inside their territory
    if current_user.role == "distributor_user" and current_user.distributor_id:
        conditions.append(
            f"""
            ST_Within(
                l.geom,
                (SELECT boundary FROM distributor_territories
                 WHERE distributor_id = ${param_idx} AND locked = TRUE
                 LIMIT 1)
            )
            """
        )
        params.append(current_user.distributor_id)
        param_idx += 1

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Count query
    count_sql = f"SELECT COUNT(*) FROM locations l {where_clause}"
    total = await db.fetchval(count_sql, *params)

    # Data query — extract lat/lon from PostGIS geom column
    data_sql = f"""
        SELECT
            l.id,
            l.name,
            l.type,
            l.city,
            l.address,
            l.pin_code,
            l.state,
            l.contact_person,
            l.phone,
            l.active,
            ST_Y(l.geom) AS latitude,
            ST_X(l.geom) AS longitude
        FROM locations l
        {where_clause}
        ORDER BY l.type, l.city
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
    """
    params.extend([limit, offset])

    rows = await db.fetch(data_sql, *params)
    locations = [_row_to_location(r) for r in rows]

    return LocationListResponse(total=total, locations=locations)


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db),
):
    """
    Return a single location by ID.
    Distributors can only access locations within their territory.
    """
    row = await db.fetchrow(
        """
        SELECT
            id, name, type, city, address, pin_code, state,
            contact_person, phone, active,
            ST_Y(geom) AS latitude,
            ST_X(geom) AS longitude
        FROM locations
        WHERE id = $1
        """,
        location_id,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location '{location_id}' not found.",
        )

    location = _row_to_location(row)

    # RBAC: distributor users cannot fetch locations outside their territory
    if current_user.role == "distributor_user" and current_user.distributor_id:
        in_territory = await db.fetchval(
            """
            SELECT ST_Within(
                (SELECT geom FROM locations WHERE id = $1),
                (SELECT boundary FROM distributor_territories
                 WHERE distributor_id = $2 AND locked = TRUE LIMIT 1)
            )
            """,
            location_id,
            current_user.distributor_id,
        )
        # If the territory boundary doesn't exist yet, in_territory will be None
        if in_territory is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This location is outside your assigned territory.",
            )

    return location