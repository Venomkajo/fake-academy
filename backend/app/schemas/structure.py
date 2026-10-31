"""Structure-shaped API payloads (README A2): fields, groups, subjects, assignments.

Public schemas shape responses and mirror the ORM columns exactly — the
/admin/structure panel already has /admin/users, so teacher/student NAMES
are resolved client-side and only FK ids travel in these payloads. The
Create/Update schemas at the bottom shape the write endpoints' bodies.
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


# --- write payloads (POST/PATCH /admin/...) --------------------------------
#
# Create schemas list the required body; Update schemas are PARTIAL —
# only the keys the client actually sends are applied (the router uses
# model_dump(exclude_unset=True)), so entities can be patched field by
# field.


class FieldOfStudyCreate(pydantic.BaseModel):
    """Body of POST /admin/fields."""

    name: str = pydantic.Field(min_length=1)


class FieldOfStudyUpdate(pydantic.BaseModel):
    """Body of PATCH /admin/fields/{id} — rename only."""

    name: str | None = pydantic.Field(default=None, min_length=1)


class StudentGroupCreate(pydantic.BaseModel):
    """Body of POST /admin/groups."""

    name: str = pydantic.Field(min_length=1)
    field_id: int


class StudentGroupUpdate(pydantic.BaseModel):
    """Body of PATCH /admin/groups/{id} — rename and/or move to another field."""

    name: str | None = pydantic.Field(default=None, min_length=1)
    field_id: int | None = None


class SubjectCreate(pydantic.BaseModel):
    """Body of POST /admin/subjects."""

    name: str = pydantic.Field(min_length=1)
    description: str | None = None


class SubjectUpdate(pydantic.BaseModel):
    """Body of PATCH /admin/subjects/{id}; explicit null clears the description."""

    name: str | None = pydantic.Field(default=None, min_length=1)
    description: str | None = None


class TeachingAssignmentCreate(pydantic.BaseModel):
    """Body of POST /admin/teaching-assignments."""

    subject_id: int
    teacher_id: int
    group_id: int


class TeachingAssignmentUpdate(pydantic.BaseModel):
    """Body of PATCH /admin/teaching-assignments/{id} — any leg may change."""

    subject_id: int | None = None
    teacher_id: int | None = None
    group_id: int | None = None


class GroupMembershipCreate(pydantic.BaseModel):
    """Body of POST /admin/group-memberships."""

    student_id: int
    group_id: int


class GroupMembershipUpdate(pydantic.BaseModel):
    """Body of PATCH /admin/group-memberships/{id} — student and/or group."""

    student_id: int | None = None
    group_id: int | None = None