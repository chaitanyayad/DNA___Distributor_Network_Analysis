from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class TerritoryCreate(BaseModel):
    """
    Request body for POST /api/territories.
    The frontend sends a GeoJSON polygon drawn on the Mapbox map.
    """
    territory_name: str = Field(..., min_length=2, max_length=100)
    distributor_id: str
    geojson_polygon: dict[str, Any] = Field(
        ...,
        description="A valid GeoJSON Polygon geometry object, e.g. "
                    '{"type": "Polygon", "coordinates": [[[lon, lat], ...]]}',
    )


class TerritoryResponse(BaseModel):
    """Single territory returned by GET /api/territories."""
    id: int
    territory_name: str
    distributor_id: str
    locked: bool
    created_at: datetime
    updated_at: datetime
    # GeoJSON polygon geometry returned as a dict for the frontend to render
    geojson: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class TerritoryLockResponse(BaseModel):
    """Returned after PATCH /api/territories/{id}/lock."""
    id: int
    territory_name: str
    locked: bool
    message: str