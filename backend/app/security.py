import datetime

import bcrypt
import jwt

from app.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET,
)


# ---------------------------------------------------------------------------
# 1. Password hashing (bcrypt)
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a plaintext password with a random bcrypt salt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # e.g. the stored value is not a valid bcrypt hash
        return False


# ---------------------------------------------------------------------------
# 2. JWT access tokens (PyJWT)
# ---------------------------------------------------------------------------

def create_access_token(user_id: int, role: str) -> str:
    """Sign a short-lived JWT carrying the user's id and role."""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Verify signature/expiry and return the claims; raises on any bad token."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
