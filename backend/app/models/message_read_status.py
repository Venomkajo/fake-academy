"""MessageReadStatus ORM model."""

import datetime

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MessageReadStatus(Base):
    """Per-user read receipts for messages (one row per recipient per message)."""

    __tablename__ = "message_read_statuses"
    __table_args__ = (
        # One receipt per user per message — a second row for the same pair
        # would always be a data-entry mistake.
        sa.UniqueConstraint("message_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # Message being tracked. Indexed because Postgres does NOT auto-index
    # FK columns, and "who read message X" filters on message_id.
    message_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("messages.id"), index=True
    )
    # Reader — users.id doubles as the student id. Indexed for
    # "unread messages of user Y".
    user_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id"), index=True
    )
    # Filled in when the user opens the message; NULL = delivered but not
    # yet read.
    read_at: Mapped[datetime.datetime | None] = mapped_column(
        sa.DateTime(timezone=True)
    )