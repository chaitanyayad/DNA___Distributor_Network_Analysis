from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from backend.config import get_settings
from backend.models.user import CurrentUser

# FastAPI's built-in Bearer token extractor
# auto_error=True means FastAPI returns 401 automatically if the
# Authorization header is missing entirely
bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    """
    Dependency injected into every protected route.

    Reads the JWT from the Authorization: Bearer <token> header,
    verifies the signature, and returns a CurrentUser object containing
    the decoded payload.

    Raises 401 if the token is missing, expired, or tampered with.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    settings = get_settings()
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str = payload.get("user_id")
        username: str = payload.get("username")
        email: str = payload.get("email")
        role: str = payload.get("role")
        distributor_id: str | None = payload.get("distributor_id")

        if user_id is None or role is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    return CurrentUser(
        user_id=user_id,
        username=username,
        email=email,
        role=role,
        distributor_id=distributor_id,
    )


def require_role(required_role: str):
    """
    Higher-order dependency factory for RBAC.

    Usage on a route:
        @router.post("/admin-only-endpoint")
        async def admin_route(
            current_user: CurrentUser = Depends(require_role("org_admin"))
        ):

    Raises 403 if the authenticated user's role does not match.
    The check happens before the route's own code runs — the route
    never executes if the role is wrong.
    """
    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. This endpoint requires role: {required_role}. "
                       f"Your role: {current_user.role}",
            )
        return current_user

    return role_checker