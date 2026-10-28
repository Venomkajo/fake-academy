"""Structure-shaped API responses (README A2): fields, groups, subjects, assignments.

These mirror the ORM columns exactly — the /admin/structure panel already
has /admin/users, so teacher/student NAMES are resolved client-side and
only FK ids travel in these payloads.
"""

import pydantic


class FieldOfStudyPublic(pydantic.BaseModel):
    """A field of study, e.g. "Computer Science", as seen by the admin panel."""

    # from_attributes (Pydantic v2) lets an endpoint hand the raw SQLAlchemy
    # row straight to response_model and let Pydantic read its attributes —
    # same trick as UserPublic.
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    name: str


class StudentGroupPublic(pydantic.BaseModel):
    """A student group, e.g. "CS-2026-A"; `field_id` links it to its field."""

    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    name: str
    field_id: int


class SubjectPublic(pydantic.BaseModel):
    """A taught subject with its optional free-form description."""

    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None


class TeachingAssignmentPublic(pydantic.BaseModel):
    """Which teacher (users.id) teaches which subject to which student group."""

    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    teacher_id: int
    group_id: int


class GroupMembershipPublic(pydantic.BaseModel):
    """One student's (users.id) membership in one student group."""

    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    student_id: int
    group_id: int


class StructureResponse(pydantic.BaseModel):
    """Payload of GET /admin/structure: every structure entity in one shot.

    The admin panel renders one tab per entity, so a single
    aggregate response covers its initial load — no five round-trips.
    """

    fields: list[FieldOfStudyPublic]
    groups: list[StudentGroupPublic]
    subjects: list[SubjectPublic]
    teaching_assignments: list[TeachingAssignmentPublic]
    group_memberships: list[GroupMembershipPublic]