"""All Pydantic schemas (request/response shapes), re-exported."""

from app.schemas.auth import LoginRequest, TokenResponse
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
from app.schemas.groups import MyGroup, TaughtGroup
from app.schemas.user import UserPublic
from app.schemas.structure import StructureResponse

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "UserPublic",
    "StructureResponse",
    "GradeCategoryCreate",
    "GradeCategoryPublic",
    "GradeCreate",
    "GradeForStudent",
    "GradeSheetResponse",
    "GradeUpdate",
    "StudentBrief",
    "StudentGradeOut",
    "TeachingAssignmentOut",
    "MyGroup",
    "TaughtGroup",
]
