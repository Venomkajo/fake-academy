"""Stats-shaped API payloads (README A4): platform-wide usage counters."""

import pydantic


class RoleCount(pydantic.BaseModel):
    """How many accounts hold one role, and how many of them are still active."""

    role: str
    total: int
    active: int


class StatsResponse(pydantic.BaseModel):
    """Payload of GET /admin/stats: every counter in one round-trip."""

    users_total: int
    users_active: int
    users_by_role: list[RoleCount]
    grades: int
    messages: int
    feedback: int
    materials: int
    lesson_slots: int
    fields_of_study: int
    student_groups: int
    subjects: int
    teaching_assignments: int
    group_memberships: int
