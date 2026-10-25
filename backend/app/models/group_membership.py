"""GroupMembership ORM model: the students-to-groups association table."""

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GroupMembership(Base):
    """Association row linking one student (user) to one student group (many-to-many)."""

    __tablename__ = "group_memberships"
    __table_args__ = (
        # A student can join a given group at most once.
        sa.UniqueConstraint("student_id", "group_id"),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # FKs are indexed because Postgres does NOT auto-index FK columns, and
    # common queries ("list groups of student X" / "members of group Y")
    # filter on either side.
    student_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id"), index=True
    )
    group_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("student_groups.id"), index=True
    )
