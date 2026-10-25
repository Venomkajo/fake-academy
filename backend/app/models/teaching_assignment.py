import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# SQLAlchemy model for the TeachingAssignment table — which teacher teaches
# which subject to which student group.
class TeachingAssignment(Base):
    __tablename__ = "teaching_assignments"
    __table_args__ = (
        # The same (subject, teacher, group) triple can be assigned at most
        # once — a duplicate would always be a data-entry mistake.
        sa.UniqueConstraint("subject_id", "teacher_id", "group_id"),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # FKs are indexed because Postgres does NOT auto-index FK columns, and
    # common queries ("what does teacher X teach?", "who teaches subject Y
    # to group Z?") filter on any of the three.
    subject_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("subjects.id"), index=True
    )
    # Teacher's account — users.id doubles as the teacher id.
    teacher_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id"), index=True
    )
    group_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("student_groups.id"), index=True
    )