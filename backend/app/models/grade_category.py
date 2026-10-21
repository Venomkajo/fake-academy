import decimal

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# SQLAlchemy model for the GradeCategory table — one row per grading bucket
# of a teaching assignment (e.g. "Exam 60%", "Homework 40%").
class GradeCategory(Base):
    __tablename__ = "grade_categories"
    __table_args__ = (
        # Category names are unique within an assignment — "Exam" twice in
        # one assignment would always be a data-entry mistake.
        sa.UniqueConstraint("assignment_id", "name"),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # The teaching assignment this category grades. Indexed because Postgres
    # does NOT auto-index FK columns, and common queries ("grade breakdown
    # of assignment X") filter on assignment_id.
    assignment_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("teaching_assignments.id"), index=True
    )
    # e.g. "Exam".
    name: Mapped[str] = mapped_column(sa.String(255))
    # Percentage share of the final grade, e.g. 60.00. Exact decimal, NOT
    # float, so rounding artefacts can never creep into grade math.
    weight: Mapped[decimal.Decimal] = mapped_column(sa.Numeric(5, 2))