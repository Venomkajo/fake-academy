import datetime
import decimal

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# SQLAlchemy model for the Grade table — one student's result in one grade
# category of one teaching assignment.
class Grade(Base):
    __tablename__ = "grades"
    __table_args__ = (
        # A student can receive at most one grade per category — a second
        # row for the same pair would be an edit, not a new grade.
        sa.UniqueConstraint("student_id", "category_id"),
        # A grade must carry SOMETHING: either a numeric value or a
        # pass/fail symbol — a row with neither is meaningless.
        sa.CheckConstraint(
            "value IS NOT NULL OR symbol IS NOT NULL",
            name="ck_grades_value_or_symbol",
        ),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # Graded student — users.id doubles as the student id (same table as
    # teachers). Indexed because Postgres does NOT auto-index FK columns.
    student_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id"), index=True
    )
    # The grade category (and through it the teaching assignment) this grade
    # belongs to. Indexed for the same reason as student_id.
    category_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("grade_categories.id"), index=True
    )
    # Numeric result, e.g. 0, 1, 2 or 2.5. Exact decimal, NOT float, so
    # "2.5" never comes back as 2.499999... Nullable because pass/fail
    # categories carry a symbol instead of a value.
    value: Mapped[decimal.Decimal | None] = mapped_column(sa.Numeric(4, 2))
    # Pass/fail symbol — "ZAL" (zaliczony, passed) / "NZAL" (niezaliczony,
    # failed). Only filled in for pass/fail categories, where `value`
    # stays NULL (enforced by the check constraint above).
    symbol: Mapped[str | None] = mapped_column(sa.String(8))
    # Filled in by the database on insert.
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(),
    )
    # Bumped by the database on every UPDATE of the row, so the audit trail
    # of "when was this grade last touched" survives row edits.
    modified_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(),
    )