import datetime

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# SQLAlchemy model for the LessonSlot table — a weekly recurring timetable
# entry ("every Tuesday, 10:15–11:45, room 3.14") of one teaching assignment.
class LessonSlot(Base):
    __tablename__ = "lesson_slots"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # Owning teaching assignment — every slot belongs to exactly one.
    # Indexed because Postgres does NOT auto-index FK columns, and common
    # queries ("timetable of assignment X") filter on assignment_id.
    assignment_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("teaching_assignments.id"), index=True
    )
    # Day of the week the slot recurs on: 0 = Monday .. 6 = Sunday — the
    # same convention as Python's date.weekday().
    day_of_week: Mapped[int] = mapped_column(sa.SmallInteger)
    # Local wall-clock boundaries of the slot. Timezone-less on purpose:
    # the school's local timezone applies, so tacking one on would be noise.
    start_time: Mapped[datetime.time] = mapped_column(sa.Time())
    end_time: Mapped[datetime.time] = mapped_column(sa.Time())
    # e.g. "Building A / room 3.14" — kept as one free-form string because
    # rooms are only ever displayed, never queried by parts.
    room: Mapped[str] = mapped_column(sa.String(255))