"""Group-shaped API payloads (early student/teacher views): whose groups these are."""

import pydantic


class MyGroup(pydantic.BaseModel):
    """One group the calling student belongs to, with its field and member count."""

    id: int
    name: str
    field_name: str
    member_count: int


class TaughtGroup(pydantic.BaseModel):
    """One of the calling teacher's assignments: which subject they teach to which group."""

    assignment_id: int
    subject_name: str
    group_id: int
    group_name: str
    field_name: str