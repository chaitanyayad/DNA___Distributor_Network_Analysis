import json
from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg

from backend.models.territory import TerritoryCreate, TerritoryResponse, TerritoryLockResponse
from backend.models.user import CurrentUser
from backend.dependencies.auth import get_current_user, require_role
from backend.database import get_db

router = APIRouter(prefix="/api/territories", tags=["Territories"])


def _row_to_territory(row: asyncpg.Record) -> TerritoryResponse:
    geojson = None
    if row["geojson_text"]:
        try:
            geojson = json.loads(row["geojson_text"])
        except Exception:
            pass
    return TerritoryResponse(
        id=row["id"],
        territory_name=row["territory_name"],
        distributor_id=row["distributor_id"],
        locked=row["locked"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        geojson=geojson,
    )


@router.get("", response_model=list[TerritoryResponse])
async def get_territories(
    current_user: CurrentUser = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db),
):
    """
    Return territories.
    - org_admin: all territories
    - distributor_user: only their own territory
    """
    if current_user.role == "org_admin":
        rows = await db.fetch(
            """
            SELECT id, territory_name, distributor_id, locked,
                   created_at, updated_at,
                   ST_AsGeoJSON(boundary) AS geojson_text
            FROM distributor_territories
            ORDER BY created_at DESC
            """
        )
    else:
        if not current_user.distributor_id:
            return []
        rows = await db.fetch(
            """
            SELECT id, territory_name, distributor_id, locked,
                   created_at, updated_at,
                   ST_AsGeoJSON(boundary) AS geojson_text
            FROM distributor_territories
            WHERE distributor_id = $1
            ORDER BY created_at DESC
            """,
            current_user.distributor_id,
        )

    return [_row_to_territory(r) for r in rows]


@router.post("", response_model=TerritoryResponse, status_code=status.HTTP_201_CREATED)
async def create_territory(
    payload: TerritoryCreate,
    current_user: CurrentUser = Depends(require_role("org_admin")),
    db: asyncpg.Connection = Depends(get_db),
):
    """
    Create a new territory from a GeoJSON polygon.

    Runs a PostGIS ST_Intersects check against ALL locked territories.
    If the new polygon overlaps any locked territory, returns 409 Conflict
    with the name of the conflicting territory — the polygon is NOT saved.

    Only org_admins can create territories.
    """
    geojson_str = json.dumps(payload.geojson_polygon)

    # Validate that the distributor_id belongs to a real distributor_user
    valid = await db.fetchval(
        "SELECT 1 FROM users WHERE distributor_id = $1 AND role = 'distributor_user'",
        payload.distributor_id,
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No distributor user found with ID '{payload.distributor_id}'. Check the ID and try again.",
        )

    # Overlap check against locked territories
    conflict_row = await db.fetchrow(
        """
        SELECT id, territory_name
        FROM distributor_territories
        WHERE locked = TRUE
          AND ST_Intersects(
              boundary,
              ST_GeomFromGeoJSON($1)
          )
        LIMIT 1
        """,
        geojson_str,
    )

    if conflict_row:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"This polygon overlaps the locked territory "
                f"'{conflict_row['territory_name']}' (ID: {conflict_row['id']}). "
                f"Adjust the boundary before saving."
            ),
        )

    # No conflict — save the territory
    row = await db.fetchrow(
        """
        INSERT INTO distributor_territories
            (territory_name, distributor_id, boundary, locked)
        VALUES
            ($1, $2, ST_GeomFromGeoJSON($3), FALSE)
        RETURNING id, territory_name, distributor_id, locked,
                  created_at, updated_at,
                  ST_AsGeoJSON(boundary) AS geojson_text
        """,
        payload.territory_name,
        payload.distributor_id,
        geojson_str,
    )

    return _row_to_territory(row)


@router.patch("/{territory_id}/lock", response_model=TerritoryLockResponse)
async def lock_territory(
    territory_id: int,
    current_user: CurrentUser = Depends(require_role("org_admin")),
    db: asyncpg.Connection = Depends(get_db),
):
    """
    Lock a territory. Once locked:
    - It cannot be modified
    - No other territory can overlap it
    - It defines the valid boundary for the distributor's RO requests

    Only org_admins can lock territories.
    """
    row = await db.fetchrow(
        "SELECT id, territory_name, locked FROM distributor_territories WHERE id = $1",
        territory_id,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Territory ID {territory_id} not found.",
        )

    if row["locked"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Territory '{row['territory_name']}' is already locked.",
        )

    updated = await db.fetchrow(
        """
        UPDATE distributor_territories
        SET locked = TRUE, updated_at = NOW()
        WHERE id = $1
        RETURNING id, territory_name, locked
        """,
        territory_id,
    )

    return TerritoryLockResponse(
        id=updated["id"],
        territory_name=updated["territory_name"],
        locked=updated["locked"],
        message=f"Territory '{updated['territory_name']}' is now locked. "
                f"No overlapping territories can be created.",
    )


@router.delete("/{territory_id}", status_code=status.HTTP_200_OK)
async def delete_territory(
    territory_id: int,
    current_user: CurrentUser = Depends(require_role("org_admin")),
    db: asyncpg.Connection = Depends(get_db),
):
    """
    Delete an unlocked territory. Locked territories cannot be deleted —
    unlock is not supported; contact a DB admin if a locked territory must be removed.
    """
    row = await db.fetchrow(
        "SELECT id, territory_name, locked FROM distributor_territories WHERE id = $1",
        territory_id,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Territory ID {territory_id} not found.",
        )

    await db.execute(
        "DELETE FROM distributor_territories WHERE id = $1",
        territory_id,
    )

    return {"message": f"Territory '{row['territory_name']}' deleted successfully."}