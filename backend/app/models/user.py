"""User accounts: one users table for students, teachers and admins alike."""

import datetime
import enum

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRole(enum.Enum):
    """Roles an account can hold; drives RBAC checks (see app/deps.py)."""

    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(Base):
    """One account per person; users.id doubles as every other table's student/teacher id."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    email: Mapped[str] = mapped_column(sa.String(255), unique=True, index=True)
    # bcrypt hash only — a plaintext password is never stored.
    password_hash: Mapped[str] = mapped_column(sa.String(255))
    first_name: Mapped[str] = mapped_column(sa.String(100))
    last_name: Mapped[str] = mapped_column(sa.String(100))
    # values_callable: store the values ('student', ...), not the enum names.
    role: Mapped[UserRole] = mapped_column(
        sa.Enum(UserRole, name="user_role", values_callable=lambda e: [m.value for m in e])
    )
    # Soft-disable switch: deactivated users get 403 at login.
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, server_default=sa.sql.expression.true())
    # Filled in by the database on insert.
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(),
    )