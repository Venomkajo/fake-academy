"""Schedule-shaped API payloads (README cards A3/S2 + teacher plan): lesson slots."""

import datetime

import pydantic


class LessonSlotOut(pydantic.BaseModel):
    """One lesson slot flattened with the names the timetable grid tiles show."""

    id: int
    assignment_id: int
    subject_name: str
    group_name: str
    field_name: str
    teacher_first_name: str
    teacher_last_name: str
    # 0 = Monday .. 6 = Sunday, same convention as the ORM column.
    day_of_week: int
    start_time: datetime.time
    end_time: datetime.time
    room: str


class LessonSlotCreate(pydantic.BaseModel):
    """Body of POST /admin/lesson-slots — one timetable entry of an assignment."""

    assignment_id: int
    day_of_week: int = pydantic.Field(ge=0, le=6)
    start_time: datetime.time
    end_time: datetime.time
    room: str = pydantic.Field(min_length=1, max_length=255)


class LessonSlotUpdate(pydantic.BaseModel):
    """Body of PATCH /admin/lesson-slots/{id}; only the sent keys change."""

    assignment_id: int | None = None
    day_of_week: int | None = pydantic.Field(default=None, ge=0, le=6)
    start_time: datetime.time | None = None
    end_time: datetime.time | None = None
    room: str | None = pydantic.Field(default=None, min_length=1, max_length=255)
