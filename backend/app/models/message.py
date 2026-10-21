import datetime

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# SQLAlchemy model for the Message table — direct user-to-user messages as
# well as announcements (ogłoszenia) sent to a whole student group.
class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        # A message must be addressed somewhere: either to one recipient
        # (individual message) or to a whole group (announcement).
        sa.CheckConstraint(
            "recipient_id IS NOT NULL OR group_id IS NOT NULL",
            name="ck_messages_recipient_or_group",
        ),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # Author's account — users.id doubles as the sender id (same table as
    # students/teachers). Indexed because Postgres does NOT auto-index FK
    # columns, and "sent mailbox of user X" filters on sender_id.
    sender_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id"), index=True
    )
    # Direct recipient — NULL for announcements (ogłoszenia), where the
    # message goes to a whole group instead. Indexed for "inbox of user X".
    recipient_id: Mapped[int | None] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id"), index=True
    )
    # Target student group — NULL for individual (person-to-person)
    # messages. Indexed for "announcements of group Y".
    group_id: Mapped[int | None] = mapped_column(
        sa.Integer, sa.ForeignKey("student_groups.id"), index=True
    )
    # Short subject line shown in inbox listings.
    title: Mapped[str] = mapped_column(sa.String(255))
    # Full message body.
    content: Mapped[str] = mapped_column(sa.Text)
    # Filled in by the database on insert.
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(),
    )