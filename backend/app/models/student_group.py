"""StudentGroup ORM model."""

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StudentGroup(Base):
    """A student group, e.g. "CS-2026-A", belonging to one field of study."""

    __tablename__ = "student_groups"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # e.g. "CS-2026-A" — not unique on its own: different fields may reuse
    # the same group name, so uniqueness is (field_id, name)-scoped at most.
    name: Mapped[str] = mapped_column(sa.String(255))
    # The field of study this group belongs to. Indexed because Postgres
    # does NOT auto-index FK columns, and common queries ("list all groups
    # of field X") filter on field_id.
    field_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("fields_of_study.id"), index=True
    )
