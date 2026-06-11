from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg

from backend.models.workflow import RORequestCreate, RORequestResponse, RORequestDecision
from backend.models.user import CurrentUser
from backend.dependencies.auth import get_current_user, require_role
from backend.database import get_db

router = APIRouter(prefix="/api/workflow", tags=["Workflow"])

# Cannibalization check distance in metres (5 km)
CANNIBALIZATION_RADIUS_M = 5000


def _row_to_ro_request(row: asyncpg.Record) -> RORequestResponse:
    return RORequestResponse(
        id=row["id"],
        requested_by=row["requested_by"],
        distributor_id=row["distributor_id"],
        proposed_name=row["proposed_name"],
        proposed_address=row["proposed_address"],
        justification=row["justification"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        status=row["status"],
        conflict_flag=row["conflict_flag"],
        admin_note=row["admin_note"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.post(
    "/request-ro",
    response_model=RORequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_ro_request(
    payload: RORequestCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db),
):
    """
    Distributor submits a new Retail Office expansion request.

    Step 1: Verify the proposed pin is inside the distributor's locked territory.
            Returns 400 if outside or if no locked territory exists.
    Step 2: Check for cannibalization — is there already a Retail Office
            within 5 km? Sets conflict_flag=TRUE if so (does not block submission).
    Step 3: Save the request as PENDING.
    """
    distributor_id = current_user.distributor_id
    if not distributor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your account has no distributor ID assigned. Contact an admin.",
        )

    # Step 1: Territory ownership check
    # ST_Within confirms the proposed point is inside this distributor's territory
    in_territory = await db.fetchval(
        """
        SELECT ST_Within(
            ST_SetSRID(ST_MakePoint($1, $2), 4326),
            (SELECT boundary FROM distributor_territories
             WHERE distributor_id = $3 AND locked = TRUE
             LIMIT 1)
        )
        """,
        payload.longitude,  # ST_MakePoint: longitude first
        payload.latitude,
        distributor_id,
    )

    if in_territory is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "You do not have a locked territory assigned. "
                "An admin must lock your territory before you can submit RO requests."
            ),
        )

    if not in_territory:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The proposed location is outside your assigned territory. "
                "Move the pin to a location within your territory boundary."
            ),
        )

    # Step 2: Cannibalization check — existing RO within 5 km?
    nearby_ro = await db.fetchval(
        """
        SELECT id FROM locations
        WHERE type = 'Retail Office'
          AND ST_DWithin(
              geom::geography,
              ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
              $3
          )
        LIMIT 1
        """,
        payload.longitude,
        payload.latitude,
        CANNIBALIZATION_RADIUS_M,
    )
    conflict_flag = nearby_ro is not None

    # Step 3: Save as PENDING
    row = await db.fetchrow(
        """
        INSERT INTO ro_requests
            (requested_by, distributor_id, proposed_name, proposed_address,
             justification, geom, status, conflict_flag)
        VALUES
            ($1, $2, $3, $4, $5,
             ST_SetSRID(ST_MakePoint($6, $7), 4326),
             'PENDING', $8)
        RETURNING
            id, requested_by, distributor_id, proposed_name, proposed_address,
            justification,
            ST_Y(geom) AS latitude, ST_X(geom) AS longitude,
            status, conflict_flag, admin_note, created_at, updated_at
        """,
        current_user.user_id,
        distributor_id,
        payload.proposed_name,
        payload.proposed_address,
        payload.justification,
        payload.longitude,
        payload.latitude,
        conflict_flag,
    )

    return _row_to_ro_request(row)


@router.get("/requests", response_model=list[RORequestResponse])
async def get_ro_requests(
    current_user: CurrentUser = Depends(require_role("org_admin")),
    db: asyncpg.Connection = Depends(get_db),
):
    """
    Admin-only: return all PENDING RO requests, newest first.
    """
    rows = await db.fetch(
        """
        SELECT
            id, requested_by, distributor_id, proposed_name, proposed_address,
            justification,
            ST_Y(geom) AS latitude, ST_X(geom) AS longitude,
            status, conflict_flag, admin_note, created_at, updated_at
        FROM ro_requests
        WHERE status = 'PENDING'
        ORDER BY created_at DESC
        """
    )
    return [_row_to_ro_request(r) for r in rows]


@router.get("/requests/all", response_model=list[RORequestResponse])
async def get_all_ro_requests(
    current_user: CurrentUser = Depends(require_role("org_admin")),
    db: asyncpg.Connection = Depends(get_db),
):
    """
    Admin-only: return all RO requests regardless of status (for history view).
    """
    rows = await db.fetch(
        """
        SELECT
            id, requested_by, distributor_id, proposed_name, proposed_address,
            justification,
            ST_Y(geom) AS latitude, ST_X(geom) AS longitude,
            status, conflict_flag, admin_note, created_at, updated_at
        FROM ro_requests
        ORDER BY created_at DESC
        """
    )
    return [_row_to_ro_request(r) for r in rows]


@router.patch("/requests/{request_id}", response_model=RORequestResponse)
async def decide_ro_request(
    request_id: int,
    decision: RORequestDecision,
    current_user: CurrentUser = Depends(require_role("org_admin")),
    db: asyncpg.Connection = Depends(get_db),
):
    """
    Admin approves or rejects an RO request.

    On APPROVED:
    - Updates ro_requests.status to APPROVED
    - Automatically inserts a new record into the locations table
      (type = 'Retail Office', active = TRUE)

    On REJECTED:
    - Updates ro_requests.status to REJECTED
    - Stores the admin's rejection note

    Raises 404 if the request doesn't exist.
    Raises 400 if the request is not in PENDING status.
    """
    # Fetch the request
    req = await db.fetchrow(
        """
        SELECT
            id, requested_by, distributor_id, proposed_name, proposed_address,
            status,
            ST_Y(geom) AS latitude, ST_X(geom) AS longitude
        FROM ro_requests
        WHERE id = $1
        """,
        request_id,
    )

    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RO request ID {request_id} not found.",
        )

    if req["status"] != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request ID {request_id} is already {req['status']}. "
                   f"Only PENDING requests can be actioned.",
        )

    if decision.action == "APPROVED":
        # Auto-create the new Retail Office in the locations table
        new_location_id = f"RO-{request_id:04d}"
        await db.execute(
            """
            INSERT INTO locations
                (id, name, type, city, address, state, active, geom)
            VALUES (
                $1, $2, 'Retail Office',
                (SELECT city FROM distributor_territories
                 WHERE distributor_id = $3 AND locked = TRUE LIMIT 1),
                $4,
                (SELECT state FROM locations
                 WHERE type = 'Dealer'
                 ORDER BY ST_Distance(
                     geom,
                     ST_SetSRID(ST_MakePoint($6, $5), 4326)
                 )
                 LIMIT 1),
                TRUE,
                ST_SetSRID(ST_MakePoint($6, $5), 4326)
            )
            ON CONFLICT (id) DO NOTHING
            """,
            new_location_id,
            req["proposed_name"],
            req["distributor_id"],
            req["proposed_address"],
            req["latitude"],
            req["longitude"],
        )

    # Update the request status
    updated = await db.fetchrow(
        """
        UPDATE ro_requests
        SET status = $1, admin_note = $2, updated_at = NOW()
        WHERE id = $3
        RETURNING
            id, requested_by, distributor_id, proposed_name, proposed_address,
            justification,
            ST_Y(geom) AS latitude, ST_X(geom) AS longitude,
            status, conflict_flag, admin_note, created_at, updated_at
        """,
        decision.action,
        decision.admin_note,
        request_id,
    )

    return _row_to_ro_request(updated)