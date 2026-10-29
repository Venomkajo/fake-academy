"""Admin domain module: admin account management, under /admin.

First endpoint: GET /admin/users — list all accounts (admin only). Later
this module grows the rest of the README's admin scope: creating
accounts, deactivating instead of deleting, role changes.
"""

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles

from app.models.field_of_study import FieldOfStudy
from app.models.group_membership import GroupMembership
from app.models.student_group import StudentGroup
from app.models.subject import Subject
from app.models.teaching_assignment import TeachingAssignment
from app.models.user import User, UserRole

from app.schemas.structure import StructureResponse
from app.schemas.user import UserPublic

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserPublic])
def list_users(
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> list[UserPublic]:
    """List every account. Admin-only."""
    users = db.scalars(sa.select(User).order_by(User.id)).all()
    # response_model=list[UserPublic] + from_attributes handles each
    # row through the allowlist, same as /auth/me — one schema guards
    # every user-shaped response in the API.
    return users

@router.get("/structure", response_model=StructureResponse)
def get_structure(
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> StructureResponse:
    """Return the whole university structure in one aggregate payload.

    Fields of study, student groups, subjects and both assignment tables —
    everything the /admin/structure panel's entity tabs need, in a single
    request. Only FK ids travel here: teacher/student names are resolved
    client-side from the /admin/users list.
    """
    return StructureResponse(
        fields=db.scalars(sa.select(FieldOfStudy).order_by(FieldOfStudy.id)).all(),
        groups=db.scalars(sa.select(StudentGroup).order_by(StudentGroup.id)).all(),
        subjects=db.scalars(sa.select(Subject).order_by(Subject.id)).all(),
        teaching_assignments=db.scalars(
            sa.select(TeachingAssignment).order_by(TeachingAssignment.id)
        ).all(),
        group_memberships=db.scalars(
            sa.select(GroupMembership).order_by(GroupMembership.id)
        ).all(),
    )

@router.get("/schedule")
def get_schedule():
    """Get the schedule of the application. Admin-only."""
    # This is a placeholder for the actual implementation.
    # You would typically query the database for the schedule information.
    return []

@router.get("/statistics")
def get_statistics():
    """Get statistics of the application. Admin-only."""
    # This is a placeholder for the actual implementation.
    # You would typically query the database for the statistics information.
    return []

@router.get("/users/{user_id}", response_model=UserPublic)
def get_user(
    user_id: int,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> UserPublic:
    """Get user information by ID. Admin-only."""
    user = db.get(User, user_id)
    if not user:
        raise sa.exc.NoResultFound(f"User with id {user_id} not found")
    return user

@router.put("/users/{user_id}", response_model=UserPublic)
def edit_user(
    user_id: int,
    updated_user: UserPublic,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> UserPublic:
    """Edit user information. Admin-only."""
    user = db.get(User, user_id)
    if not user:
        raise sa.exc.NoResultFound(f"User with id {user_id} not found")

    for field in ['first_name', 'last_name', 'email', 'role', 'is_active']:
        if getattr(updated_user, field) is None:
            raise ValueError(f"{field} cannot be None")

    # Update user fields with new information
    user.first_name = updated_user.first_name
    user.last_name = updated_user.last_name
    user.email = updated_user.email
    user.role = updated_user.role
    user.is_active = updated_user.is_active

    db.commit()
    db.refresh(user)

    return user
