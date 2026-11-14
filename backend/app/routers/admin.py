"""Admin domain module: accounts and university structure, under /admin.

Account management (/admin/users) plus the README A2 structure scope:
GET /admin/structure displays everything, and one POST/PATCH/DELETE
triple per entity (fields, groups, subjects, teaching assignments,
group memberships) edits it. Every route here is admin-only.
"""

import datetime

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles

from app.models.field_of_study import FieldOfStudy
from app.models.feedback import Feedback
from app.models.grade import Grade
from app.models.group_membership import GroupMembership
from app.models.lesson_slot import LessonSlot
from app.models.material import Material
from app.models.message import Message
from app.models.student_group import StudentGroup
from app.models.subject import Subject
from app.models.teaching_assignment import TeachingAssignment
from app.models.user import User, UserRole

from app.routers.schedule import fetch_slot_row, fetch_slot_rows
from app.schemas.schedule import (
    LessonSlotCreate,
    LessonSlotOut,
    LessonSlotUpdate,
)
from app.schemas.stats import RoleCount, StatsResponse
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
from app.schemas.user import UserPublic, UserUpdate

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
# One POST/PATCH/DELETE triple per entity, mirroring GET /admin/structure
# above. PATCH bodies are partial: only the sent keys are applied; a
# DELETE that would orphan FK children ends in a 409 instead.


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


@router.delete("/fields/{field_id}", status_code=204)
def delete_field(
    field_id: int,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> None:
    """Delete a field of study. Admin-only."""
    field = _get_or_404(db, FieldOfStudy, field_id, "kierunek")
    db.delete(field)
    _commit_or_conflict(db, "Nie można usunąć kierunku — istnieją powiązane grupy")


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


@router.delete("/groups/{group_id}", status_code=204)
def delete_group(
    group_id: int,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> None:
    """Delete a student group. Admin-only."""
    group = _get_or_404(db, StudentGroup, group_id, "grupa")
    db.delete(group)
    _commit_or_conflict(db, "Nie można usunąć grupy — ma przypisania lub członków")


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


@router.delete("/subjects/{subject_id}", status_code=204)
def delete_subject(
    subject_id: int,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> None:
    """Delete a subject. Admin-only."""
    subject = _get_or_404(db, Subject, subject_id, "przedmiot")
    db.delete(subject)
    _commit_or_conflict(db, "Nie można usunąć przedmiotu — ma materiały lub przypisania")


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


@router.delete("/teaching-assignments/{assignment_id}", status_code=204)
def delete_teaching_assignment(
    assignment_id: int,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> None:
    """Delete a teaching assignment. Admin-only."""
    assignment = _get_or_404(db, TeachingAssignment, assignment_id, "przypisanie")
    db.delete(assignment)
    _commit_or_conflict(
        db, "Nie można usunąć przypisania — mają do niego zajęcia lub kategorie ocen"
    )


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


@router.delete("/group-memberships/{membership_id}", status_code=204)
def delete_group_membership(
    membership_id: int,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> None:
    """Remove a student from a group. Admin-only."""
    membership = _get_or_404(db, GroupMembership, membership_id, "członkostwo")
    db.delete(membership)
    _commit_or_conflict(db, "Nie można usunąć członkostwa")


# --- lesson slots: the timetable editor (README A3) ------------------------
#
# One weekly recurring entry per teaching assignment. The hard part is
# collision validation: within one day, a room, a student group and a
# teacher may each be busy in at most one lesson — overlapping slots are
# rejected with a 409 naming the exact clashing lesson.


def _check_slot_conflicts(
    db: Session,
    slot_id: int | None,
    assignment: TeachingAssignment,
    day: int,
    start: datetime.time,
    end: datetime.time,
    room: str,
) -> None:
    """Reject a slot that double-books a room, a group or a teacher (400/409)."""
    if start >= end:
        raise HTTPException(
            status_code=400,
            detail="Godzina zakończenia musi być późniejsza niż godzina rozpoczęcia",
        )
    # Candidates: same-day slots whose time window overlaps the proposed one
    # (start < other.end AND other.start < end). The joined names let the
    # 409 message name the exact clashing lesson instead of a bare id.
    query = (
        sa.select(LessonSlot, TeachingAssignment, User, StudentGroup, Subject)
        .join(TeachingAssignment, TeachingAssignment.id == LessonSlot.assignment_id)
        .join(User, User.id == TeachingAssignment.teacher_id)
        .join(StudentGroup, StudentGroup.id == TeachingAssignment.group_id)
        .join(Subject, Subject.id == TeachingAssignment.subject_id)
        .where(
            LessonSlot.day_of_week == day,
            LessonSlot.start_time < end,
            LessonSlot.end_time > start,
        )
    )
    if slot_id is not None:
        # A PATCH excludes the row being edited from its own conflict check.
        query = query.where(LessonSlot.id != slot_id)
    for other_slot, other_assignment, teacher, group, subject in db.execute(query):
        hours = f"{other_slot.start_time:%H:%M}–{other_slot.end_time:%H:%M}"
        if other_slot.room == room:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Sala „{room}” jest już zajęta: {subject.name}, "
                    f"grupa {group.name}, {hours}"
                ),
            )
        if other_assignment.group_id == assignment.group_id:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Grupa {group.name} ma już wtedy zajęcia: {subject.name}, "
                    f"sala {other_slot.room}, {hours}"
                ),
            )
        if other_assignment.teacher_id == assignment.teacher_id:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"{teacher.first_name} {teacher.last_name} prowadzi już wtedy "
                    f"zajęcia: {subject.name}, grupa {group.name}, {hours}"
                ),
            )


@router.get("/lesson-slots", response_model=list[LessonSlotOut])
def list_lesson_slots(
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> list[LessonSlotOut]:
    """Return every lesson slot with subject/teacher/group names. Admin-only."""
    return fetch_slot_rows(db)


@router.post("/lesson-slots", response_model=LessonSlotOut, status_code=201)
def create_lesson_slot(
    body: LessonSlotCreate,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> LessonSlotOut:
    """Add one timetable slot to a teaching assignment. Admin-only."""
    assignment = _get_or_404(db, TeachingAssignment, body.assignment_id, "przypisanie")
    _check_slot_conflicts(
        db,
        None,
        assignment,
        body.day_of_week,
        body.start_time,
        body.end_time,
        body.room,
    )
    slot = LessonSlot(
        assignment_id=assignment.id,
        day_of_week=body.day_of_week,
        start_time=body.start_time,
        end_time=body.end_time,
        room=body.room,
    )
    db.add(slot)
    _commit_or_conflict(db, "Nie można dodać zajęć")
    # The flattened response (with the joined names) is one extra read, not
    # a second write path.
    out = fetch_slot_row(db, slot.id)
    if out is None:  # unreachable: the row was committed above
        raise HTTPException(status_code=500, detail="Nie udało się odczytać zajęć")
    return out


@router.patch("/lesson-slots/{slot_id}", response_model=LessonSlotOut)
def edit_lesson_slot(
    slot_id: int,
    body: LessonSlotUpdate,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> LessonSlotOut:
    """Change any leg of a lesson slot (assignment, day, time, room). Admin-only."""
    slot = _get_or_404(db, LessonSlot, slot_id, "zajęcia")
    updates = body.model_dump(exclude_unset=True)
    assignment_id = updates.get("assignment_id", slot.assignment_id)
    assignment = _get_or_404(db, TeachingAssignment, assignment_id, "przypisanie")
    # Conflict check on the EFFECTIVE values: keys the client sent override,
    # the rest keep the row's current values.
    _check_slot_conflicts(
        db,
        slot.id,
        assignment,
        updates.get("day_of_week", slot.day_of_week),
        updates.get("start_time", slot.start_time),
        updates.get("end_time", slot.end_time),
        updates.get("room", slot.room),
    )
    for key, value in updates.items():
        setattr(slot, key, value)
    _commit_or_conflict(db, "Nie można zapisać zajęć")
    out = fetch_slot_row(db, slot.id)
    if out is None:  # unreachable: the row was committed above
        raise HTTPException(status_code=500, detail="Nie udało się odczytać zajęć")
    return out


@router.delete("/lesson-slots/{slot_id}", status_code=204)
def delete_lesson_slot(
    slot_id: int,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> None:
    """Delete a lesson slot from the timetable. Admin-only."""
    # Lesson topics hang off the assignment, not the slot, so a slot has no
    # FK children and can always be removed.
    slot = _get_or_404(db, LessonSlot, slot_id, "zajęcia")
    db.delete(slot)
    _commit_or_conflict(db, "Nie można usunąć zajęć")

@router.get("/stats", response_model=StatsResponse)
def get_statistics(
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> StatsResponse:
    """Return platform-wide usage counters (README A4). Admin-only."""
    # Accounts: one grouped query returns per-role total + active counts —
    # SUM over a CASE marks active rows as 1, deactivated as 0.
    role_rows = db.execute(
        sa.select(
            User.role,
            sa.func.count(User.id),
            sa.func.sum(sa.case((User.is_active, 1), else_=0)),
        ).group_by(User.role)
    ).all()
    by_role = {
        role.value: RoleCount(
            role=role.value, total=total, active=int(active or 0)
        )
        for role, total, active in role_rows
    }
    # All three roles stay present even when one has zero accounts, so the
    # dashboard's chart never needs to handle a missing row.
    for role in UserRole:
        by_role.setdefault(role.value, RoleCount(role=role.value, total=0, active=0))

    def _count_rows(model: type) -> int:
        """Count every row of one table with a single aggregate."""
        return db.scalar(sa.select(sa.func.count(model.id)))

    return StatsResponse(
        users_total=sum(item.total for item in by_role.values()),
        users_active=sum(item.active for item in by_role.values()),
        users_by_role=[by_role[role.value] for role in UserRole],
        grades=_count_rows(Grade),
        messages=_count_rows(Message),
        feedback=_count_rows(Feedback),
        materials=_count_rows(Material),
        lesson_slots=_count_rows(LessonSlot),
        fields_of_study=_count_rows(FieldOfStudy),
        student_groups=_count_rows(StudentGroup),
        subjects=_count_rows(Subject),
        teaching_assignments=_count_rows(TeachingAssignment),
        group_memberships=_count_rows(GroupMembership),
    )

@router.get("/users/{user_id}", response_model=UserPublic)
def get_user(
    user_id: int,
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> UserPublic:
    """Get one account's data by id. Admin-only."""
    # _get_or_404, not a bare db.get + raise NoResultFound: an unknown id
    # must answer 404, not blow up as an unhandled 500.
    return _get_or_404(db, User, user_id, "użytkownik")

@router.patch("/users/{user_id}", response_model=UserPublic)
def edit_user(
    user_id: int,
    body: UserUpdate,
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> UserPublic:
    """Edit an account's data, role or active flag. Admin-only (README A1)."""
    
    user = _get_or_404(db, User, user_id, "użytkownik")
    updates = body.model_dump(exclude_unset=True)

    if user.id == admin.id and (
        ("role" in updates and updates["role"] != user.role)
        or ("is_active" in updates and not updates["is_active"])
    ):
        raise HTTPException(
            status_code=400,
            detail="Nie można zmienić własnej roli ani dezaktywować własnego konta",
        )

    for key, value in updates.items():
        setattr(user, key, value)
    # A taken email (users.email is unique) lands here as 409, not a 500.
    _commit_or_conflict(db, "Nie można zapisać zmian — e-mail może być zajęty")
    db.refresh(user)
    return user
