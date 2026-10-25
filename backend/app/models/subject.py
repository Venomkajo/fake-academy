"""Subject ORM model."""

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Subject(Base):
    """A taught subject, e.g. "Algorithms and Data Structures"."""

    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # e.g. "Algorithms and Data Structures".
    name: Mapped[str] = mapped_column(sa.String(255))
    # Longer, free-form course description; nullable because a subject
    # can exist before anyone writes its syllabus.
    description: Mapped[str | None] = mapped_column(sa.Text)
