import datetime

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# SQLAlchemy model for the Feedback table — a teacher's free-form comment on
# one dated lesson topic.
class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # The lesson topic this comment belongs to. Indexed because Postgres
    # does NOT auto-index FK columns, and common queries ("feedback for
    # topic X") filter on topic_id.
    topic_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("lesson_topics.id"), index=True
    )
    # Comment author — users.id doubles as the teacher id (confirmed).
    author_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id"), index=True
    )
    # Free-form comment body.
    content: Mapped[str] = mapped_column(sa.Text)
    # Filled in by the database on insert.
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(),
    )