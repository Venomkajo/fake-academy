"""Grade-shaped API payloads (README cards S1/W1/W2): viewing and issuing grades."""

import datetime
import decimal

import pydantic


class GradeForStudent(pydantic.BaseModel):
    """One grade of the calling student, flattened with the names the view groups by."""

    id: int
    value: decimal.Decimal | None
    symbol: str | None
    created_at: datetime.datetime
    modified_at: datetime.datetime
    category_name: str
    category_weight: decimal.Decimal
    subject_name: str
    teacher_first_name: str
    teacher_last_name: str
    group_name: str


class GradeCategoryPublic(pydantic.BaseModel):
    """One grading bucket of a teaching assignment, e.g. 'Egzamin 60%'."""

    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    name: str
    weight: decimal.Decimal


class TeachingAssignmentOut(pydantic.BaseModel):
    """One of the caller's teaching assignments: subject x group plus its categories."""

    id: int
    subject_name: str
    group_name: str
    field_name: str
    categories: list[GradeCategoryPublic]


class StudentBrief(pydantic.BaseModel):
    """A student's identity for gradebook rows (never the email or hash)."""

    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str


class StudentGradeOut(pydantic.BaseModel):
    """One gradebook cell: the grade itself with its student and category ids."""

    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    student_id: int
    category_id: int
    value: decimal.Decimal | None
    symbol: str | None


class GradeSheetResponse(pydantic.BaseModel):
    """Payload of the teacher's gradebook: the group's students and their grades."""

    students: list[StudentBrief]
    grades: list[StudentGradeOut]


class GradeCategoryCreate(pydantic.BaseModel):
    """Body of POST /grades/categories — a name and a percentage weight."""

    assignment_id: int
    name: str = pydantic.Field(min_length=1)
    weight: decimal.Decimal = pydantic.Field(ge=0, le=100)


class GradeCreate(pydantic.BaseModel):
    """Body of POST /grades — exactly one of value/symbol must be sent."""

    student_id: int
    category_id: int
    value: decimal.Decimal | None = pydantic.Field(default=None, ge=0, le=100)
    symbol: str | None = pydantic.Field(default=None, pattern="^(ZAL|NZAL)$")


class GradeUpdate(pydantic.BaseModel):
    """Body of PATCH /grades/{id}; an explicitly sent null clears that field."""

    value: decimal.Decimal | None = pydantic.Field(default=None, ge=0, le=100)
    symbol: str | None = pydantic.Field(default=None, pattern="^(ZAL|NZAL)$")