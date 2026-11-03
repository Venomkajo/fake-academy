"""Grades domain module (/grades): student's own grades, teacher's gradebook."""

import decimal

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models.field_of_study import FieldOfStudy
from app.models.grade import Grade
from app.models.grade_category import GradeCategory
from app.models.group_membership import GroupMembership
from app.models.student_group import StudentGroup
from app.models.subject import Subject
from app.models.teaching_assignment import TeachingAssignment
from app.models.user import User, UserRole

from app.schemas.grades import (
    GradeCategoryCreate,
    GradeCategoryPublic,
    GradeCreate,
    GradeForStudent,
    GradeSheetResponse,
    GradeUpdate,
    StudentBrief,
    StudentGradeOut,
    TeachingAssignmentOut,
)

router = APIRouter(prefix="/grades", tags=["grades"])


# --- shared helpers ---------------------------------------------------------
#
# Same guard pattern as app/routers/admin.py: 404 for a missing row, 403 when
# the row exists but is not the caller's, 409 for uniqueness conflicts.


def _owned_assignment(db: Session, assignment_id: int, teacher: User) -> TeachingAssignment:
    """Fetch an assignment or raise 404/403 unless the caller teaches it."""
    assignment = db.get(TeachingAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(
            status_code=404, detail=f"Nie znaleziono (przypisanie id={assignment_id})"
        )
    if assignment.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="To przypisanie nie jest Twoje")
    return assignment


def _owned_category(db: Session, category_id: int, teacher: User) -> GradeCategory:
    """Fetch a grade category whose assignment the caller must teach."""
    category = db.get(GradeCategory, category_id)
    if category is None:
        raise HTTPException(
            status_code=404, detail=f"Nie znaleziono (kategoria id={category_id})"
        )
    _owned_assignment(db, category.assignment_id, teacher)
    return category


def _check_value_or_symbol(value: decimal.Decimal | None, symbol: str | None) -> None:
    """Require exactly one of the numeric value and the ZAL/NZAL symbol."""
    if (value is None) == (symbol is None):
        raise HTTPException(
            status_code=400,
            detail="Ocena musi mieć dokładnie jedną wartość: liczbę albo symbol ZAL/NZAL",
        )


def _commit_or_conflict(db: Session, conflict_detail: str) -> None:
    """Commit, translating a constraint violation into a 409."""
    try:
        db.commit()
    except sa.exc.IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=conflict_detail)


# --- reads ------------------------------------------------------------------


@router.get("/me", response_model=list[GradeForStudent])
def my_grades(
    student: User = Depends(require_roles(UserRole.STUDENT)),
    db: Session = Depends(get_db),
) -> list[GradeForStudent]:
    """Return the calling student's grades, flattened with category/subject/teacher names."""
    rows = db.execute(
        sa.select(Grade, GradeCategory, TeachingAssignment, Subject, StudentGroup, User)
        .join(GradeCategory, GradeCategory.id == Grade.category_id)
        .join(TeachingAssignment, TeachingAssignment.id == GradeCategory.assignment_id)
        .join(Subject, Subject.id == TeachingAssignment.subject_id)
        .join(StudentGroup, StudentGroup.id == TeachingAssignment.group_id)
        .join(User, User.id == TeachingAssignment.teacher_id)
        .where(Grade.student_id == student.id)
        .order_by(Subject.name, StudentGroup.name, GradeCategory.name)
    ).all()
    return [
        GradeForStudent(
            id=grade.id,
            value=grade.value,
            symbol=grade.symbol,
            created_at=grade.created_at,
            modified_at=grade.modified_at,
            category_name=category.name,
            category_weight=category.weight,
            subject_name=subject.name,
            teacher_first_name=teacher.first_name,
            teacher_last_name=teacher.last_name,
            group_name=group.name,
        )
        for grade, category, _assignment, subject, group, teacher in rows
    ]


@router.get("/teaching", response_model=list[TeachingAssignmentOut])
def my_teaching(
    teacher: User = Depends(require_roles(UserRole.TEACHER)),
    db: Session = Depends(get_db),
) -> list[TeachingAssignmentOut]:
    """Return the calling teacher's assignments (subject × group) with their grade categories."""
    assignments = db.execute(
        sa.select(TeachingAssignment, Subject, StudentGroup, FieldOfStudy)
        .join(Subject, Subject.id == TeachingAssignment.subject_id)
        .join(StudentGroup, StudentGroup.id == TeachingAssignment.group_id)
        .join(FieldOfStudy, FieldOfStudy.id == StudentGroup.field_id)
        .where(TeachingAssignment.teacher_id == teacher.id)
        .order_by(FieldOfStudy.name, StudentGroup.name, Subject.name)
    ).all()

    categories = db.scalars(
        sa.select(GradeCategory)
        .where(GradeCategory.assignment_id.in_([a.id for a, *_ in assignments]))
        .order_by(GradeCategory.id)
    ).all()

    by_assignment: dict[int, list[GradeCategoryPublic]] = {}
    for category in categories:
        by_assignment.setdefault(category.assignment_id, []).append(
            GradeCategoryPublic.model_validate(category)
        )

    return [
        TeachingAssignmentOut(
            id=assignment.id,
            subject_name=subject.name,
            group_name=group.name,
            field_name=field.name,
            categories=by_assignment.get(assignment.id, []),
        )
        for assignment, subject, group, field in assignments
    ]


@router.get("/assignment/{assignment_id}/sheet", response_model=GradeSheetResponse)
def gradebook_sheet(
    assignment_id: int,
    teacher: User = Depends(require_roles(UserRole.TEACHER)),
    db: Session = Depends(get_db),
) -> GradeSheetResponse:
    """Return one of the caller's assignments as a gradebook: students plus their grades."""
    assignment = _owned_assignment(db, assignment_id, teacher)

    students = db.scalars(
        sa.select(User)
        .join(GroupMembership, GroupMembership.student_id == User.id)
        .where(
            GroupMembership.group_id == assignment.group_id,
            User.role == UserRole.STUDENT,
        )
        .order_by(User.last_name, User.first_name)
    ).all()

    grades = db.scalars(
        sa.select(Grade)
        .join(GradeCategory, GradeCategory.id == Grade.category_id)
        .where(GradeCategory.assignment_id == assignment.id)
        .order_by(Grade.id)
    ).all()

    return GradeSheetResponse(
        students=[StudentBrief.model_validate(student) for student in students],
        grades=[StudentGradeOut.model_validate(grade) for grade in grades],
    )


# --- writes -----------------------------------------------------------------


@router.post("/categories", response_model=GradeCategoryPublic, status_code=201)
def create_grade_category(
    body: GradeCategoryCreate,
    teacher: User = Depends(require_roles(UserRole.TEACHER)),
    db: Session = Depends(get_db),
) -> GradeCategoryPublic:
    """Create a grade category in one of the caller's assignments."""
    _owned_assignment(db, body.assignment_id, teacher)
    category = GradeCategory(
        assignment_id=body.assignment_id,
        name=body.name,
        weight=body.weight,
    )
    db.add(category)
    _commit_or_conflict(db, "Ta kategoria już istnieje w tym przypisaniu")
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=204)
def delete_grade_category(
    category_id: int,
    teacher: User = Depends(require_roles(UserRole.TEACHER)),
    db: Session = Depends(get_db),
) -> None:
    """Delete a grade category owned by the caller; a category with grades stays (409)."""
    category = _owned_category(db, category_id, teacher)
    has_grades = (
        db.scalar(sa.select(Grade.id).where(Grade.category_id == category.id).limit(1))
        is not None
    )
    if has_grades:
        raise HTTPException(
            status_code=409,
            detail="Kategoria ma wystawione oceny — nie można jej usunąć",
        )
    db.delete(category)
    _commit_or_conflict(db, "Nie można usunąć kategorii")


@router.post("", response_model=StudentGradeOut, status_code=201)
def issue_grade(
    body: GradeCreate,
    teacher: User = Depends(require_roles(UserRole.TEACHER)),
    db: Session = Depends(get_db),
) -> StudentGradeOut:
    """Issue one grade (value or ZAL/NZAL symbol) to a student of the caller's group."""
    category = _owned_category(db, body.category_id, teacher)
    assignment = db.get(TeachingAssignment, category.assignment_id)

    student = db.get(User, body.student_id)
    if student is None:
        raise HTTPException(
            status_code=404, detail=f"Nie znaleziono (student id={body.student_id})"
        )
    is_member = (
        db.scalar(
            sa.select(GroupMembership.id).where(
                GroupMembership.student_id == student.id,
                GroupMembership.group_id == assignment.group_id,
            )
        )
        is not None
    )
    if not is_member:
        raise HTTPException(
            status_code=400, detail="Student nie należy do grupy tego przypisania"
        )

    _check_value_or_symbol(body.value, body.symbol)

    grade = Grade(
        student_id=student.id,
        category_id=category.id,
        value=body.value,
        symbol=body.symbol,
    )
    db.add(grade)
    _commit_or_conflict(db, "Ten student ma już ocenę w tej kategorii")
    db.refresh(grade)
    return grade


@router.patch("/{grade_id}", response_model=StudentGradeOut)
def edit_grade(
    grade_id: int,
    body: GradeUpdate,
    teacher: User = Depends(require_roles(UserRole.TEACHER)),
    db: Session = Depends(get_db),
) -> StudentGradeOut:
    """Edit an existing grade's value or symbol; keys sent as null clear them."""
    grade = db.get(Grade, grade_id)
    if grade is None:
        raise HTTPException(status_code=404, detail=f"Nie znaleziono (ocena id={grade_id})")
    _owned_category(db, grade.category_id, teacher)

    # Effective pair after the partial update — validated BEFORE applying,
    # so a row never ends up violating the value-or-symbol check constraint.
    value = body.value if "value" in body.model_fields_set else grade.value
    symbol = body.symbol if "symbol" in body.model_fields_set else grade.symbol
    _check_value_or_symbol(value, symbol)

    grade.value = value
    grade.symbol = symbol
    _commit_or_conflict(db, "Nie można zapisać oceny")
    db.refresh(grade)
    return grade