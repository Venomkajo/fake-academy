import datetime
import enum

import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# Enum for notification types
class NotificationType(enum.Enum):
    GRADE = "grade"
    MESSAGE = "message"
    FEEDBACK = "feedback"
    PLAN_CHANGE = "plan_change"


# SQLAlchemy model for the Notification table — one inbox entry per event
# (new grade, new message, ...), shown in the user's notification bell.
class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # Owner — users.id doubles as the recipient id. Indexed because
    # Postgres does NOT auto-index FK columns, and the single most common
    # query, "unread notifications of user X", filters on user_id.
    user_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id"), index=True
    )
    # values_callable: store the values ('grade', ...), not the enum names.
    type: Mapped[NotificationType] = mapped_column(
        sa.Enum(
            NotificationType,
            name="notification_type",
            values_callable=lambda e: [m.value for m in e],
        )
    )
    # Event-specific data, e.g. {"grade_id": 42, "subject": "Algorithms"}.
    # JSONB (not JSON): indexed/containing operators work on it server-side.
    payload: Mapped[dict] = mapped_column(JSONB)
    # Filled in by the database on insert.
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(),
    )
    # NULL = not yet read; filled in when the user opens the notification.
    read_at: Mapped[datetime.datetime | None] = mapped_column(
        sa.DateTime(timezone=True)
    )