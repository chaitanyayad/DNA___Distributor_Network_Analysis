from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import asyncpg

from backend.models.user import LoginRequest, TokenResponse
from backend.database import get_db
from backend.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiry_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: asyncpg.Connection = Depends(get_db),
):
    """
    Authenticate a user and return a JWT token.

    - Looks up the user by email
    - Verifies the password against the stored bcrypt hash
    - Returns a signed JWT containing user_id, role, and distributor_id
    - Token is valid for JWT_EXPIRY_MINUTES (default 480 = 8 hours)
    """
    row = await db.fetchrow(
        """
        SELECT id, username, email, hashed_password, role, distributor_id
        FROM users
        WHERE email = $1
        """,
        login_data.email,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with that email address.",
        )

    if not verify_password(login_data.password, row["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password.",
        )

    token_payload = {
        "user_id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "role": row["role"],
        "distributor_id": row["distributor_id"],
    }

    access_token = create_access_token(token_payload)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=row["role"],
        user_id=row["id"],
        distributor_id=row["distributor_id"],
        username=row["username"],
    )


@router.post("/logout")
async def logout():
    """
    Stateless logout — instructs the frontend to discard the token.
    JWTs are self-contained; the server has no session to invalidate.
    The frontend removes the token from React state on receiving this response.
    """
    return {"message": "Logged out successfully. Please discard your token."}