from pydantic import BaseModel, Field
from typing import Optional


class LocationResponse(BaseModel):
    """
    Single location record returned by GET /api/locations and
    GET /api/locations/{location_id}.

    Note: latitude and longitude are extracted from the PostGIS geom column
    using ST_Y(geom) and ST_X(geom) respectively in the SQL query — they are
    NOT separate columns in the database.
    """
    id: str
    name: str
    type: str
    city: str
    address: Optional[str] = None
    pin_code: Optional[str] = None
    state: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    active: bool
    latitude: float
    longitude: float

    model_config = {"from_attributes": True}


class LocationListResponse(BaseModel):
    """Paginated wrapper returned by GET /api/locations."""
    total: int
    locations: list[LocationResponse]


class MarketGridCell(BaseModel):
    """
    One cell from the market_potential_grid table.
    Returned by GET /api/analytics/hotspots.
    """
    grid_id: str
    latitude: float
    longitude: float
    vehicle_count: int
    predicted_revenue_inr: Optional[float] = None
    hotspot_score: Optional[float] = None
    is_white_space: bool = False

    model_config = {"from_attributes": True}


class WhiteSpaceResponse(BaseModel):
    """
    White-space pocket returned by GET /api/analytics/whitespaces.
    These are DBSCAN cluster centroids flagged as untapped opportunities.
    """
    grid_id: str
    latitude: float
    longitude: float
    vehicle_count: int
    hotspot_score: Optional[float] = None

    model_config = {"from_attributes": True}