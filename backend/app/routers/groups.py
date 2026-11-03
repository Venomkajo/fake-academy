"""Groups the caller belongs to or teaches (/groups): early student/teacher views."""

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

from app.schemas.groups import MyGroup, TaughtGroup

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("/me", response_model=list[MyGroup])
def my_groups(
    student: User = Depends(require_roles(UserRole.STUDENT)),
    db: Session = Depends(get_db),
) -> list[MyGroup]:
    """Return the calling student's groups with field names and member counts."""
    groups = db.execute(
        sa.select(StudentGroup, FieldOfStudy)
        .join(FieldOfStudy, FieldOfStudy.id == StudentGroup.field_id)
        .join(GroupMembership, GroupMembership.group_id == StudentGroup.id)
        .where(GroupMembership.student_id == student.id)
        .order_by(FieldOfStudy.name, StudentGroup.name)
    ).all()

    # Member counts for JUST these groups, in one grouped query — the count
    # covers every member, not only the caller.
    counts = dict(
        db.execute(
            sa.select(GroupMembership.group_id, sa.func.count(GroupMembership.id))
            .where(GroupMembership.group_id.in_([group.id for group, _ in groups]))
            .group_by(GroupMembership.group_id)
        ).all()
    )

    return [
        MyGroup(
            id=group.id,
            name=group.name,
            field_name=field.name,
            member_count=counts.get(group.id, 0),
        )
        for group, field in groups
    ]


@router.get("/teaching", response_model=list[TaughtGroup])
def taught_groups(
    teacher: User = Depends(require_roles(UserRole.TEACHER)),
    db: Session = Depends(get_db),
) -> list[TaughtGroup]:
    """Return the groups the calling teacher teaches, with subject and field names."""
    rows = db.execute(
        sa.select(TeachingAssignment, Subject, StudentGroup, FieldOfStudy)
        .join(Subject, Subject.id == TeachingAssignment.subject_id)
        .join(StudentGroup, StudentGroup.id == TeachingAssignment.group_id)
        .join(FieldOfStudy, FieldOfStudy.id == StudentGroup.field_id)
        .where(TeachingAssignment.teacher_id == teacher.id)
        .order_by(FieldOfStudy.name, StudentGroup.name, Subject.name)
    ).all()
    return [
        TaughtGroup(
            assignment_id=assignment.id,
            subject_name=subject.name,
            group_id=group.id,
            group_name=group.name,
            field_name=field.name,
        )
        for assignment, subject, group, field in rows
    ]