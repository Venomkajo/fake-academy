"""Users domain module: admin account management, under /users.

First endpoint: GET /admin/users — list all accounts (admin only). Later
this module grows the rest of the README's admin scope: creating
accounts, deactivating instead of deleting, role changes.
"""

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models.user import User, UserRole
from app.schemas.user import UserPublic

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserPublic])
def list_users(
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> list[UserPublic]:
    """List every account. Admin-only.
    """
    users = db.scalars(sa.select(User).order_by(User.id)).all()
    # response_model=list[UserPublic] + from_attributes handles each
    # row through the allowlist, same as /auth/me — one schema guards
    # every user-shaped response in the API.
    return users