import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security import decode_access_token

# HTTPBearer is a ready-made dependency that:
#   - reads the `Authorization` request header,
#   - requires the "Bearer" scheme (Authorization: Bearer <token>),
#   - hands us the token part as HTTPAuthorizationCredentials.

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the caller from their Bearer token — or raise 401/403.

    Used by every protected endpoint as `Depends(get_current_user)`.
    If it returns, the endpoint code can simply ASSUME it is talking
    to a real, authenticated, active user.
    """
    # 1. Header present? ("Authorization: Bearer ...")
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Signature valid and not expired? (jwt.decode does both.)
    try:
        claims = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        # Catch-all for every other JWT problem.
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Token names a user that actually exists?
    # "sub" is whatever string we signed at login time (our convention:
    # the user id). We validate rather than trust: int() will raise on
    # anything that isn't a clean integer.
    try:
        user_id = int(claims["sub"])
    except (KeyError, ValueError):
        # A token WE signed always has a valid "sub" — this branch only
        # fires for tokens from a different/older/buggy issuer, or a
        # compromised secret. Treat as invalid.
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # db.get() is the shortcut for SELECT ... WHERE id = <pk>.
    user = db.get(User, user_id)
    if user is None:
        # Signature valid, but the account is gone. The caller is effectively
        # nobody -> 401.
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Still active?
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    return user