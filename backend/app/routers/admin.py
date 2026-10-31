"""Admin domain module: accounts and university structure, under /admin.

Account management (/admin/users) plus the README A2 structure scope:
GET /admin/structure displays everything, and one POST/PATCH pair per
entity (fields, groups, subjects, teaching assignments, group
memberships) edits it. Every route here is admin-only.
"""

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles

from app.models.field_of_study import FieldOfStudy
from app.models.group_membership import GroupMembership
from app.models.student_group import StudentGroup
from app.models.subject import Subject
from app.models.teaching_assignment import TeachingAssignment
from app.models.user import User, UserRole

from app.schemas.structure import (
    FieldOfStudyCreate,
    FieldOfStudyPublic,
    FieldOfStudyUpdate,
    GroupMembershipCreate,
    GroupMembershipPublic,
    GroupMembershipUpdate,
    StudentGroupCreate,
    StudentGroupPublic,
    StudentGroupUpdate,
    SubjectCreate,
    SubjectPublic,
    SubjectUpdate,
    StructureResponse,
    TeachingAssignmentCreate,
    TeachingAssignmentPublic,
    TeachingAssignmentUpdate,
)
from app.schemas.user import UserPublic

router = APIRouter(prefix="/admin", tags=["admin"])


# --- shared helpers for the structure write endpoints ----------------------
#
# Three guards reused by every POST/PATCH below: 404 for a missing row or
# FK target, 400 when a user FK does not hold the expected role, 409 when
# a unique constraint (or the one-group-per-field rule) rejects the write.


def _get_or_404(db: Session, model: type, row_id: int, what: str):
    """Fetch a row by primary key or raise a 404 with a Polish message."""
    row = db.get(model, row_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Nie znaleziono ({what} id={row_id})")
    return row


def _require_user_role(db: Session, user_id: int, role: UserRole) -> None:
    """Ensure the referenced user exists and holds `role` (400 otherwise)."""
    user = _get_or_404(db, User, user_id, "użytkownik")
    if user.role != role:
        raise HTTPException(
            status_code=400,
            detail=f"Użytkownik {user.email} nie ma roli '{role.value}'",
        )


def _commit_or_conflict(db: Session, conflict_detail: str) -> None:
    """Commit, translating a unique-constraint violation into a 409."""
    try:
        db.commit()
    except sa.exc.IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=conflict_detail)


def _validate_membership_rules(
    db: Session, student_id: int, group_id: int, exclude_id: int | None = None
) -> None:
    """Check a membership's FKs, the student role and the one-group-per-field rule."""
    _require_user_role(db, student_id, UserRole.STUDENT)
    group = _get_or_404(db, StudentGroup, group_id, "grupa")
    # README A2 consistency rule: a student may belong to at most ONE group
    # per field of study — a second group on the same field is a mistake.
    query = (
        sa.select(GroupMembership)
        .join(StudentGroup, StudentGroup.id == GroupMembership.group_id)
        .where(
            GroupMembership.student_id == student_id,
            StudentGroup.field_id == group.field_id,
        )
    )
    if exclude_id is not None:
        # A PATCH excludes the row being edited from its own conflict check.
        query = query.where(GroupMembership.id != exclude_id)
    if db.scalar(query) is not None:
        raise HTTPException(
            status_code=409,
            detail="Student należy już do innej grupy na tym kierunku",
        )


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

# --- structure write endpoints (README A2) ---------------------------------
#
# One POST/PATCH pair per entity, mirroring GET /admin/structure above.
# PATCH bodies are partial: only the keys the client sends are applied.


@router.post("/fields", response_model=FieldOfStudyPublic, status_code=201)
def create_field(
    body: FieldOfStudyCreate,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> FieldOfStudyPublic:
    """Create a field of study. Admin-only."""
    field = FieldOfStudy(name=body.name)
    db.add(field)
    _commit_or_conflict(db, "Kierunek o tej nazwie już istnieje")
    db.refresh(field)
    return field


@router.patch("/fields/{field_id}", response_model=FieldOfStudyPublic)
def edit_field(
    field_id: int,
    body: FieldOfStudyUpdate,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> FieldOfStudyPublic:
    """Rename a field of study. Admin-only."""
    field = _get_or_404(db, FieldOfStudy, field_id, "kierunek")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(field, key, value)
    _commit_or_conflict(db, "Kierunek o tej nazwie już istnieje")
    db.refresh(field)
    return field


@router.post("/groups", response_model=StudentGroupPublic, status_code=201)
def create_group(
    body: StudentGroupCreate,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> StudentGroupPublic:
    """Create a student group inside an existing field. Admin-only."""
    _get_or_404(db, FieldOfStudy, body.field_id, "kierunek")
    group = StudentGroup(name=body.name, field_id=body.field_id)
    db.add(group)
    _commit_or_conflict(db, "Konflikt danych grupy")
    db.refresh(group)
    return group


@router.patch("/groups/{group_id}", response_model=StudentGroupPublic)
def edit_group(
    group_id: int,
    body: StudentGroupUpdate,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> StudentGroupPublic:
    """Rename a group or move it to another field. Admin-only."""
    group = _get_or_404(db, StudentGroup, group_id, "grupa")
    updates = body.model_dump(exclude_unset=True)
    if "field_id" in updates:
        _get_or_404(db, FieldOfStudy, updates["field_id"], "kierunek")
    for key, value in updates.items():
        setattr(group, key, value)
    _commit_or_conflict(db, "Konflikt danych grupy")
    db.refresh(group)
    return group


@router.post("/subjects", response_model=SubjectPublic, status_code=201)
def create_subject(
    body: SubjectCreate,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> SubjectPublic:
    """Create a subject. Admin-only."""
    subject = Subject(name=body.name, description=body.description)
    db.add(subject)
    _commit_or_conflict(db, "Konflikt danych przedmiotu")
    db.refresh(subject)
    return subject


@router.patch("/subjects/{subject_id}", response_model=SubjectPublic)
def edit_subject(
    subject_id: int,
    body: SubjectUpdate,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> SubjectPublic:
    """Edit a subject; an explicitly sent null clears the description. Admin-only."""
    subject = _get_or_404(db, Subject, subject_id, "przedmiot")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(subject, key, value)
    _commit_or_conflict(db, "Konflikt danych przedmiotu")
    db.refresh(subject)
    return subject


@router.post(
    "/teaching-assignments", response_model=TeachingAssignmentPublic, status_code=201
)
def create_teaching_assignment(
    body: TeachingAssignmentCreate,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> TeachingAssignmentPublic:
    """Assign a teacher to a subject for one student group. Admin-only."""
    _get_or_404(db, Subject, body.subject_id, "przedmiot")
    _require_user_role(db, body.teacher_id, UserRole.TEACHER)
    _get_or_404(db, StudentGroup, body.group_id, "grupa")
    assignment = TeachingAssignment(
        subject_id=body.subject_id, teacher_id=body.teacher_id, group_id=body.group_id
    )
    db.add(assignment)
    _commit_or_conflict(db, "Ten wykładowca już prowadzi ten przedmiot w tej grupie")
    db.refresh(assignment)
    return assignment


@router.patch(
    "/teaching-assignments/{assignment_id}", response_model=TeachingAssignmentPublic
)
def edit_teaching_assignment(
    assignment_id: int,
    body: TeachingAssignmentUpdate,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> TeachingAssignmentPublic:
    """Change any leg of an existing teaching assignment. Admin-only."""
    assignment = _get_or_404(db, TeachingAssignment, assignment_id, "przypisanie")
    updates = body.model_dump(exclude_unset=True)
    if "subject_id" in updates:
        _get_or_404(db, Subject, updates["subject_id"], "przedmiot")
    if "teacher_id" in updates:
        _require_user_role(db, updates["teacher_id"], UserRole.TEACHER)
    if "group_id" in updates:
        _get_or_404(db, StudentGroup, updates["group_id"], "grupa")
    for key, value in updates.items():
        setattr(assignment, key, value)
    _commit_or_conflict(db, "Ten wykładowca już prowadzi ten przedmiot w tej grupie")
    db.refresh(assignment)
    return assignment


@router.post("/group-memberships", response_model=GroupMembershipPublic, status_code=201)
def create_group_membership(
    body: GroupMembershipCreate,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> GroupMembershipPublic:
    """Put a student into a group. Admin-only."""
    _validate_membership_rules(db, body.student_id, body.group_id)
    membership = GroupMembership(student_id=body.student_id, group_id=body.group_id)
    db.add(membership)
    _commit_or_conflict(db, "Student należy już do tej grupy")
    db.refresh(membership)
    return membership


@router.patch("/group-memberships/{membership_id}", response_model=GroupMembershipPublic)
def edit_group_membership(
    membership_id: int,
    body: GroupMembershipUpdate,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> GroupMembershipPublic:
    """Change a membership's student, group or both. Admin-only."""
    membership = _get_or_404(db, GroupMembership, membership_id, "członkostwo")
    # The one-group-per-field rule is checked on the EFFECTIVE pair: keys
    # the client sent override, the rest keep the row's current values.
    student_id = body.student_id if body.student_id is not None else membership.student_id
    group_id = body.group_id if body.group_id is not None else membership.group_id
    _validate_membership_rules(db, student_id, group_id, exclude_id=membership.id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(membership, key, value)
    _commit_or_conflict(db, "Student należy już do tej grupy")
    db.refresh(membership)
    return membership


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
