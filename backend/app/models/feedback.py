"""Feedback ORM model: students' comments on lesson topics."""

import datetime

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Feedback(Base):
    """A student's comment on a lesson topic.

    author_id is only used to verify that the student actually attended
    the lesson, and is never returned by the API.
    """

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # The lesson topic this comment belongs to. Indexed because Postgres
    # does NOT auto-index FK columns, and common queries ("feedback for
    # topic X") filter on topic_id.
    topic_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("lesson_topics.id"), index=True
    )
    # Comment author — users.id doubles as the student id.
    author_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id"), index=True
    )
    # Free-form comment body.
    content: Mapped[str] = mapped_column(sa.Text)
    # Filled in by the database on insert.
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(),
    )