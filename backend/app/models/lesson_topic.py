import datetime

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# SQLAlchemy model for the LessonTopic table — what was (or will be) taught
# during a particular dated lesson of one teaching assignment.
class LessonTopic(Base):
    __tablename__ = "lesson_topics"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # The teaching assignment this topic belongs to. Indexed because
    # Postgres does NOT auto-index FK columns, and common queries ("topic
    # history of assignment X") filter on assignment_id.
    assignment_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("teaching_assignments.id"), index=True
    )
    # e.g. "Quicksort — partitioning strategies".
    topic: Mapped[str] = mapped_column(sa.String(255))
    # Calendar date of the lesson — not a full timestamp, because the time
    # of day comes from the assignment's lesson slots.
    lesson_date: Mapped[datetime.date] = mapped_column(sa.Date())
    # Teacher who entered the topic — users.id doubles as the teacher id
    # (confirmed), so this FK also targets users.
    created_by: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id"), index=True
    )