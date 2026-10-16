import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserPublic
from app.security import create_access_token, hash_password, verify_password

# All routes in this file live under /auth and get an "auth" tag in
# the OpenAPI/Swagger docs (grouping in the UI).
router = APIRouter(prefix="/auth", tags=["auth"])

# A bcrypt hash of a password nobody knows. Computed once at import
# (costs ~0.2s) — used below to defend against a TIMING ATTACK.
_DUMMY_HASH = hash_password("no-such-user-timing-equalizer")


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Exchange email + password for a signed JWT access token."""
    # Depends(get_db): FastAPI calls get_db() for this request, hands
    # us the session, and closes it afterwards (see app/database.py).

    user = db.scalar(sa.select(User).where(User.email == body.email))

    if user is None:
        # Unknown email. We STILL run a full bcrypt check against a
        # dummy hash before answering: bcrypt takes ~0.2s, so without
        # this, "no such user" would answer instantly while "wrong
        # password" would answer slowly — an attacker could measure
        # response times to check which emails exist in the system
        # (user enumeration via timing side channel).
        verify_password(body.password, _DUMMY_HASH)
        raise _invalid_credentials()

    if not verify_password(body.password, user.password_hash):
        # Same generic error as above: identical message, identical
        # status code. The API never reveals WHICH part was wrong.
        raise _invalid_credentials()

    # Only past this point are the credentials proven correct, so a
    # more specific error no longer leaks anything: the caller already
    # knows the password. 403 = "authenticated, but forbidden" —
    # distinct from 401 = "I don't know who you are".
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token(user_id=user.id, role=user.role.value)

    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    """Who am I? The frontend calls this right after login to fill its
    user context (name in the navbar, role-based menu, ...).
    """
    return current_user


def _invalid_credentials() -> HTTPException:
    # Generic 401 for any login failure (unknown email or wrong password).
    return HTTPException(
        status_code=401,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
