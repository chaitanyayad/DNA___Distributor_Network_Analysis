from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RORequestCreate(BaseModel):
    """
    Request body for POST /api/workflow/request-ro.
    The distributor drops a pin on the map and fills in the form.
    """
    proposed_name: str = Field(..., min_length=2, max_length=200)
    proposed_address: Optional[str] = None
    justification: Optional[str] = None
    latitude: float = Field(..., ge=6.0, le=37.6)
    longitude: float = Field(..., ge=68.0, le=97.5)


class RORequestResponse(BaseModel):
    """Single RO request record."""
    id: int
    requested_by: str
    distributor_id: str
    proposed_name: str
    proposed_address: Optional[str] = None
    justification: Optional[str] = None
    latitude: float
    longitude: float
    status: str                        # PENDING / APPROVED / REJECTED
    conflict_flag: bool
    admin_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RORequestDecision(BaseModel):
    """
    Request body for PATCH /api/workflow/requests/{id}.
    Admin sends their decision.
    """
    action: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    admin_note: Optional[str] = None


class AnalyticsSummary(BaseModel):
    """
    Returned by GET /api/analytics/summary.
    Populates the KPI cards on the admin dashboard.
    """
    total_locations: int
    active_locations: int
    total_territories: int
    locked_territories: int
    pending_ro_requests: int
    total_predicted_revenue_inr: float
    locations_by_type: dict[str, int]