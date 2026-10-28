"""Seed the database with development users and a fake university structure.

Idempotent: every entity is matched by its natural key (user email,
field/subject name, (field, group) pair, assignment/membership FK set)
and existing rows are skipped, so it is safe to run again at any time.

The structure half covers README card A2 (Struktura uczelni): fields of
study own student groups, subjects stand alone, teaching assignments tie
a teacher to a subject for a group, and memberships tie students to
groups. Rows reference each other by NAME/email and the script resolves
ids at runtime, so the seed never depends on serial values that differ
between machines.

Note: importing app.security (indirectly) requires JWT_SECRET to be
set — app/config.py fails fast without it — even though seeding only
hashes passwords and never signs tokens.
"""

import sys
from pathlib import Path

# Make `import app...` work no matter where this file is run from.
# Normally Python only searches the script's OWN directory (scripts/)
# for imports, so we explicitly add backend/ (one level up).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Console encoding fix so Polish names print correctly on Windows.
sys.stdout.reconfigure(encoding="utf-8")

import sqlalchemy as sa  # noqa: E402 — must come AFTER the sys.path tweak
from sqlalchemy.orm import Session  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.field_of_study import FieldOfStudy  # noqa: E402
from app.models.group_membership import GroupMembership  # noqa: E402
from app.models.student_group import StudentGroup  # noqa: E402
from app.models.subject import Subject  # noqa: E402
from app.models.teaching_assignment import TeachingAssignment  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.security import hash_password  # noqa: E402


# (email, first_name, last_name, role, dev_password, is_active)
# Passwords are deliberately trivial: this is dev-only data, and it
# makes the login flow easy to test per role.
SEED_USERS = [
    ("admin@fake.academy", "Jan", "Nowak", UserRole.ADMIN, "admin123!", True),
    ("anna@fake.academy", "Anna", "Kowalska", UserRole.TEACHER, "teacher123!", True),
    ("piotr@fake.academy", "Piotr", "Zieliński", UserRole.TEACHER, "teacher123!", True),
    ("kasia@fake.academy", "Kasia", "Wiśniewska", UserRole.STUDENT, "student123!", True),
    ("marek@fake.academy", "Marek", "Lewandowski", UserRole.STUDENT, "student123!", True),
    ("ewa@fake.academy", "Ewa", "Kozłowska", UserRole.STUDENT, "student123!", True),
    # Deactivated on purpose: correct password, but login must give 403.
    ("zdzislaw@fake.academy", "Zdzisław", "Wyłączony", UserRole.STUDENT, "student123!", False),
]

# Fields of study: just the (unique) name.
SEED_FIELDS = [
    "Computer Science",
    "Mathematics",
]

# (field_name, group_name) — a group belongs to exactly one field.
SEED_GROUPS = [
    ("Computer Science", "CS-2026-A"),
    ("Computer Science", "CS-2026-B"),
    ("Mathematics", "MATH-2026-A"),
]

# (name, description) — description is nullable; Calculus shows that.
SEED_SUBJECTS = [
    (
        "Algorithms and Data Structures",
        "Complexity, sorting, graphs — and when to reach for which one.",
    ),
    ("Databases", "Relational modelling, SQL and transactions."),
    ("Calculus", None),
    ("Linear Algebra", "Vectors, matrices and eigenvectors."),
]

# (subject_name, teacher_email, field_name, group_name): one teacher
# teaches one subject to one group. The same subject may have a
# different teacher for a different group (Databases below) — only the
# exact (subject, teacher, group) triple is unique.
SEED_TEACHING_ASSIGNMENTS = [
    (
        "Algorithms and Data Structures",
        "anna@fake.academy",
        "Computer Science",
        "CS-2026-A",
    ),
    ("Databases", "anna@fake.academy", "Computer Science", "CS-2026-A"),
    ("Databases", "piotr@fake.academy", "Computer Science", "CS-2026-B"),
    ("Calculus", "piotr@fake.academy", "Mathematics", "MATH-2026-A"),
    ("Linear Algebra", "piotr@fake.academy", "Mathematics", "MATH-2026-A"),
]

# (student_email, field_name, group_name) — at most one group per field
# per student (README A2 consistency rule). zdzislaw stays a member of
# CS-2026-B although his account is deactivated: membership is history,
# and history is never deleted (README A1).
SEED_GROUP_MEMBERSHIPS = [
    ("kasia@fake.academy", "Computer Science", "CS-2026-A"),
    ("marek@fake.academy", "Computer Science", "CS-2026-A"),
    ("zdzislaw@fake.academy", "Computer Science", "CS-2026-B"),
    ("ewa@fake.academy", "Mathematics", "MATH-2026-A"),
]


def _field_by_name(db: Session, name: str) -> FieldOfStudy:
    """Resolve a seed-referenced field of study; fail loudly if missing."""
    field = db.scalar(sa.select(FieldOfStudy).where(FieldOfStudy.name == name))
    if field is None:
        raise SystemExit(f"seed references field {name!r}, but it does not exist")
    return field


def _subject_by_name(db: Session, name: str) -> Subject:
    """Resolve a seed-referenced subject; fail loudly if missing."""
    subject = db.scalar(sa.select(Subject).where(Subject.name == name))
    if subject is None:
        raise SystemExit(f"seed references subject {name!r}, but it does not exist")
    return subject


def _user_by_email(db: Session, email: str) -> User:
    """Resolve a seed-referenced account; fail loudly if missing."""
    user = db.scalar(sa.select(User).where(User.email == email))
    if user is None:
        raise SystemExit(f"seed references user {email!r}, but no such user exists")
    return user


def _group_by_name(db: Session, field_name: str, group_name: str) -> StudentGroup:
    """Resolve a seed-referenced group within its field; fail loudly if missing."""
    field = _field_by_name(db, field_name)
    group = db.scalar(
        sa.select(StudentGroup).where(
            StudentGroup.field_id == field.id, StudentGroup.name == group_name
        )
    )
    if group is None:
        raise SystemExit(
            f"seed references group {group_name!r} of field {field_name!r},"
            " but it does not exist"
        )
    return group



def seed_users(db: Session) -> int:
    """Insert any seed users that are missing; return how many were added."""
    inserted = 0
    print("Seeding users:")
    for email, first_name, last_name, role, password, is_active in SEED_USERS:
        exists = db.scalar(sa.select(User).where(User.email == email))
        if exists is not None:
            print(f"  skip (already exists): {email}")
            continue

        db.add(
            User(
                email=email,
                # Store ONLY the bcrypt hash — same rule as the
                # API: a plaintext password never touches the DB.
                password_hash=hash_password(password),
                first_name=first_name,
                last_name=last_name,
                role=role,
                is_active=is_active,
            )
        )
        inserted += 1
        note = "" if is_active else "  <- deactivated on purpose"
        print(f"  add: {email:<24} {role.value:<8} password={password}{note}")
    return inserted



def seed_fields(db: Session) -> int:
    """Insert missing fields of study; return how many were added."""
    inserted = 0
    print("Seeding fields of study:")
    for name in SEED_FIELDS:
        exists = db.scalar(sa.select(FieldOfStudy).where(FieldOfStudy.name == name))
        if exists is not None:
            print(f"  skip (already exists): {name}")
            continue

        db.add(FieldOfStudy(name=name))
        inserted += 1
        print(f"  add: {name}")
    return inserted


def seed_groups(db: Session) -> int:
    """Insert missing student groups; return how many were added."""
    inserted = 0
    print("Seeding student groups:")
    for field_name, name in SEED_GROUPS:
        field = _field_by_name(db, field_name)
        exists = db.scalar(
            sa.select(StudentGroup).where(
                StudentGroup.field_id == field.id, StudentGroup.name == name
            )
        )
        if exists is not None:
            print(f"  skip (already exists): {field_name} / {name}")
            continue

        db.add(StudentGroup(name=name, field_id=field.id))
        inserted += 1
        print(f"  add: {name:<12} field={field_name}")
    return inserted


def seed_subjects(db: Session) -> int:
    """Insert missing subjects; return how many were added."""
    inserted = 0
    print("Seeding subjects:")
    for name, description in SEED_SUBJECTS:
        exists = db.scalar(sa.select(Subject).where(Subject.name == name))
        if exists is not None:
            print(f"  skip (already exists): {name}")
            continue

        db.add(Subject(name=name, description=description))
        inserted += 1
        has_desc = "" if description is None else " (with description)"
        print(f"  add: {name}{has_desc}")
    return inserted



def seed_teaching_assignments(db: Session) -> int:
    """Insert missing teaching assignments; return how many were added."""
    inserted = 0
    print("Seeding teaching assignments:")
    for subject_name, teacher_email, field_name, group_name in SEED_TEACHING_ASSIGNMENTS:
        subject = _subject_by_name(db, subject_name)
        teacher = _user_by_email(db, teacher_email)
        group = _group_by_name(db, field_name, group_name)
        exists = db.scalar(
            sa.select(TeachingAssignment).where(
                TeachingAssignment.subject_id == subject.id,
                TeachingAssignment.teacher_id == teacher.id,
                TeachingAssignment.group_id == group.id,
            )
        )
        if exists is not None:
            print(f"  skip (already exists): {teacher_email} / {subject_name} / {group_name}")
            continue

        db.add(
            TeachingAssignment(
                subject_id=subject.id, teacher_id=teacher.id, group_id=group.id
            )
        )
        inserted += 1
        print(f"  add: {group_name:<12} {subject_name} <- {teacher_email}")
    return inserted


def seed_group_memberships(db: Session) -> int:
    """Insert missing group memberships; return how many were added."""
    inserted = 0
    print("Seeding group memberships:")
    for student_email, field_name, group_name in SEED_GROUP_MEMBERSHIPS:
        student = _user_by_email(db, student_email)
        group = _group_by_name(db, field_name, group_name)
        exists = db.scalar(
            sa.select(GroupMembership).where(
                GroupMembership.student_id == student.id,
                GroupMembership.group_id == group.id,
            )
        )
        if exists is not None:
            print(f"  skip (already exists): {student_email} / {group_name}")
            continue

        db.add(GroupMembership(student_id=student.id, group_id=group.id))
        inserted += 1
        print(f"  add: {group_name:<12} {student_email}")
    return inserted


def main() -> None:
    """Seed everything that is missing: users first, then the structure referencing them."""
    db = SessionLocal()
    try:
        # Steps run parents-first (users → fields → groups → subjects →
        # assignments → memberships) so every reference exists before it
        # is looked up. db.flush() after each step makes freshly-added
        # rows visible to the next step's SELECTs — SessionLocal is
        # autoflush=False, so this does NOT happen automatically.
        inserted = seed_users(db)
        db.flush()
        inserted += seed_fields(db)
        db.flush()
        inserted += seed_groups(db)
        db.flush()
        inserted += seed_subjects(db)
        db.flush()
        inserted += seed_teaching_assignments(db)
        db.flush()
        inserted += seed_group_memberships(db)

        # One commit at the end: either all inserts succeed or none.
        db.commit()

        expected = (
            len(SEED_USERS)
            + len(SEED_FIELDS)
            + len(SEED_GROUPS)
            + len(SEED_SUBJECTS)
            + len(SEED_TEACHING_ASSIGNMENTS)
            + len(SEED_GROUP_MEMBERSHIPS)
        )
        print(f"Done: {inserted} inserted, {expected - inserted} skipped.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
