import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# SQLAlchemy model for the FieldOfStudy table
class FieldOfStudy(Base):
    __tablename__ = "fields_of_study"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # e.g. "Computer Science" — unique, because it is the natural
    # human-facing identifier of a field.
    name: Mapped[str] = mapped_column(sa.String(255), unique=True)
