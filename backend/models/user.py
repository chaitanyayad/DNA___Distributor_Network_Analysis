from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    """Request body for POST /api/auth/login."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Returned on successful login."""
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    distributor_id: Optional[str] = None
    username: str


class CurrentUser(BaseModel):
    """
    Decoded JWT payload — attached to every protected request by the
    get_current_user dependency. Not a database model; lives in memory only.
    """
    user_id: int
    username: str
    email: str
    role: str                          # "org_admin" or "distributor_user"
    distributor_id: Optional[str] = None   # None for org_admins