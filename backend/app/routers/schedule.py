"""Schedule domain module (/schedule): the caller's weekly timetable.

Two read-only views (README S2 for students, the matching teacher view):
GET /schedule/me returns the slots of every group the student belongs to,
GET /schedule/teaching returns the slots of the teacher's own assignments.
Slots are weekly recurring (no dates), so no week parameter exists — the
frontend's week navigation only relabels the columns' dates.
"""

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models.field_of_study import FieldOfStudy
from app.models.group_membership import GroupMembership
from app.models.lesson_slot import LessonSlot
from app.models.student_group import StudentGroup
from app.models.subject import Subject
from app.models.teaching_assignment import TeachingAssignment
from app.models.user import User, UserRole

from app.schemas.schedule import LessonSlotOut

router = APIRouter(prefix="/schedule", tags=["schedule"])


def _slot_query() -> sa.Select:
    """Build the slot join: slot rows plus subject/group/field/teacher names."""
    return (
        sa.select(
            LessonSlot,
            Subject.name,
            StudentGroup.name,
            FieldOfStudy.name,
            User.first_name,
            User.last_name,
        )
        .join(TeachingAssignment, TeachingAssignment.id == LessonSlot.assignment_id)
        .join(Subject, Subject.id == TeachingAssignment.subject_id)
        .join(StudentGroup, StudentGroup.id == TeachingAssignment.group_id)
        .join(FieldOfStudy, FieldOfStudy.id == StudentGroup.field_id)
        .join(User, User.id == TeachingAssignment.teacher_id)
        .order_by(LessonSlot.day_of_week, LessonSlot.start_time)
    )


def _to_slot_out(row: tuple) -> LessonSlotOut:
    """Map one joined query row into a flattened LessonSlotOut."""
    (
        slot,
        subject_name,
        group_name,
        field_name,
        teacher_first_name,
        teacher_last_name,
    ) = row
    return LessonSlotOut(
        id=slot.id,
        assignment_id=slot.assignment_id,
        subject_name=subject_name,
        group_name=group_name,
        field_name=field_name,
        teacher_first_name=teacher_first_name,
        teacher_last_name=teacher_last_name,
        day_of_week=slot.day_of_week,
        start_time=slot.start_time,
        end_time=slot.end_time,
        room=slot.room,
    )


def fetch_slot_rows(
    db: Session, assignment_ids: list[int] | None = None
) -> list[LessonSlotOut]:
    """Return lesson slots flattened with subject/group/field/teacher names.

    `assignment_ids=None` means every slot in the university (the admin
    editor); otherwise only slots of those assignments. Shared with the
    admin router so every schedule-shaped read goes through one query.
    """
    query = _slot_query()
    if assignment_ids is not None:
        query = query.where(LessonSlot.assignment_id.in_(assignment_ids))
    return [_to_slot_out(row) for row in db.execute(query)]


def fetch_slot_row(db: Session, slot_id: int) -> LessonSlotOut | None:
    """Return one flattened slot by its id, or None when the id is unknown."""
    row = db.execute(_slot_query().where(LessonSlot.id == slot_id)).first()
    return None if row is None else _to_slot_out(row)


@router.get("/me", response_model=list[LessonSlotOut])
def my_schedule(
    student: User = Depends(require_roles(UserRole.STUDENT)),
    db: Session = Depends(get_db),
) -> list[LessonSlotOut]:
    """Return the weekly slots of every group the calling student belongs to."""
    assignment_ids = db.scalars(
        sa.select(TeachingAssignment.id)
        .join(GroupMembership, GroupMembership.group_id == TeachingAssignment.group_id)
        .where(GroupMembership.student_id == student.id)
    ).all()
    return fetch_slot_rows(db, assignment_ids)


@router.get("/teaching", response_model=list[LessonSlotOut])
def teaching_schedule(
    teacher: User = Depends(require_roles(UserRole.TEACHER)),
    db: Session = Depends(get_db),
) -> list[LessonSlotOut]:
    """Return the weekly slots of every assignment the calling teacher holds."""
    assignment_ids = db.scalars(
        sa.select(TeachingAssignment.id).where(
            TeachingAssignment.teacher_id == teacher.id
        )
    ).all()
    return fetch_slot_rows(db, assignment_ids)
