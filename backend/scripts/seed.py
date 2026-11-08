"""Seed the database with dev users, university structure and sample grades.

Idempotent: every entity is matched by its natural key (user email,
field/subject name, (field, group) pair, assignment/membership FK set,
(assignment, category name) pair, (student, category) pair) and existing
rows are skipped, so it is safe to run again at any time.

The structure half covers README card A2 (Struktura uczelni): fields of
study own student groups, subjects stand alone, teaching assignments tie
a teacher to a subject for a group, and memberships tie students to
groups. On top of that, grade categories and a handful of sample grades
cover the early student/teacher views (README S1/W1/W2), and a weekly
timetable of lesson slots covers the schedule views (README A3/S2).
Rows reference each other by NAME/email and the script resolves ids at
runtime, so the seed never depends on serial values that differ between
machines.

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

import decimal  # noqa: E402 — stdlib, grouped with the app imports below
import datetime  # noqa: E402

import sqlalchemy as sa  # noqa: E402 — must come AFTER the sys.path tweak
from sqlalchemy.orm import Session  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.field_of_study import FieldOfStudy  # noqa: E402
from app.models.grade import Grade  # noqa: E402
from app.models.grade_category import GradeCategory  # noqa: E402
from app.models.group_membership import GroupMembership  # noqa: E402
from app.models.lesson_slot import LessonSlot  # noqa: E402
from app.models.message import Message  # noqa: E402
from app.models.message_read_status import MessageReadStatus  # noqa: E402
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

# (teacher_email, subject_name, field_name, group_name, day_of_week, start, end,
#  room) — the weekly timetable of each seeded assignment (README A3/S2).
# day_of_week: 0 = Monday .. 6 = Sunday; blocks are the typical 90 minutes.
# The set below deliberately respects all three conflict rules (room, group,
# teacher) so it stays insertable through the same validation the API uses.
SEED_LESSON_SLOTS = [
    ("anna@fake.academy", "Algorithms and Data Structures", "Computer Science", "CS-2026-A", 0, "10:15", "11:45", "A-3.14"),
    ("anna@fake.academy", "Algorithms and Data Structures", "Computer Science", "CS-2026-A", 3, "08:00", "09:30", "A-3.14"),
    ("anna@fake.academy", "Databases", "Computer Science", "CS-2026-A", 1, "09:45", "11:15", "B-1.07"),
    ("anna@fake.academy", "Databases", "Computer Science", "CS-2026-A", 2, "13:00", "14:30", "B-0.11"),
    ("piotr@fake.academy", "Databases", "Computer Science", "CS-2026-B", 1, "11:30", "13:00", "B-1.07"),
    ("piotr@fake.academy", "Databases", "Computer Science", "CS-2026-B", 4, "10:15", "11:45", "B-1.07"),
    ("piotr@fake.academy", "Calculus", "Mathematics", "MATH-2026-A", 0, "08:00", "09:30", "C-2.01"),
    ("piotr@fake.academy", "Calculus", "Mathematics", "MATH-2026-A", 2, "11:15", "12:45", "C-2.01"),
    ("piotr@fake.academy", "Linear Algebra", "Mathematics", "MATH-2026-A", 3, "11:15", "12:45", "C-2.01"),
    ("piotr@fake.academy", "Linear Algebra", "Mathematics", "MATH-2026-A", 4, "13:00", "14:30", "C-1.10"),
]

# (sender_email, recipient_email | (field_name, group_name), title | None, content,
#  minutes_ago): a private chat between a student and a teacher (no title —
# chat needs none) plus two group announcements (titled). Sample data for
# the messages views (README S3/W4). Recipient is either a person (string)
# or a group (pair); minutes_ago staggers created_at so the reply ALWAYS
# follows the question chronologically (Postgres now() is the transaction
# start, so unstamped rows would all share one timestamp).
SEED_MESSAGES = [
    (
        "kasia@fake.academy",
        "anna@fake.academy",
        None,
        "Dzień dobry,\n\nczy projektu z baz danych można oddawać w parach?",
        2900,
    ),
    (
        "anna@fake.academy",
        "kasia@fake.academy",
        None,
        "Dzień dobry,\n\ntak, projekty można oddawać w parach — tylko proszę zaznaczyć to w raporcie.",
        2880,
    ),
    (
        "anna@fake.academy",
        ("Computer Science", "CS-2026-A"),
        "Zmiana terminu konsultacji",
        "Dzień dobry,\n\nkonsultacje w ten czwartek odbędą się o 16:00 zamiast 15:00.\n\nPozdrawiam,\nAnna Kowalska",
        1440,
    ),
    (
        "piotr@fake.academy",
        ("Mathematics", "MATH-2026-A"),
        "Kolokwium z algebry liniowej",
        "Dzień dobry,\n\nkolokwium z algebry liniowej odbędzie się na zajęciach w przyszły wtorek. Obowiązuje materiał z wykładów 1–5.",
        90,
    ),
]

# (reader_email, message_index) — read receipts so the unread counters and
# the read/unread state have something realistic to show: kasia has read the
# first message of her thread, nothing else.
SEED_MESSAGE_READS = [
    ("kasia@fake.academy", 0),
]
# grading buckets of each assignment. Weights are percentages; they sum to
# 100 per assignment where a full breakdown exists.
# (teacher_email, subject_name, field_name, group_name, category_name, weight):
SEED_GRADE_CATEGORIES = [
    ("anna@fake.academy", "Algorithms and Data Structures", "Computer Science", "CS-2026-A", "Egzamin", 60),
    ("anna@fake.academy", "Algorithms and Data Structures", "Computer Science", "CS-2026-A", "Kolokwium", 25),
    ("anna@fake.academy", "Algorithms and Data Structures", "Computer Science", "CS-2026-A", "Aktywność", 15),
    ("anna@fake.academy", "Databases", "Computer Science", "CS-2026-A", "Projekt", 50),
    ("anna@fake.academy", "Databases", "Computer Science", "CS-2026-A", "Egzamin", 50),
    ("piotr@fake.academy", "Calculus", "Mathematics", "MATH-2026-A", "Egzamin", 100),
    ("piotr@fake.academy", "Linear Algebra", "Mathematics", "MATH-2026-A", "Kolokwium", 40),
    ("piotr@fake.academy", "Linear Algebra", "Mathematics", "MATH-2026-A", "Egzamin", 60),
]

# (student_email, teacher_email, subject_name, field_name, group_name,
#  category_name, value, symbol) — sample grades for the early views.
# value XOR symbol per the grades check constraint; "ZAL" demonstrates the
# pass/fail path (Databases Projekt).
SEED_GRADES = [
    ("kasia@fake.academy", "anna@fake.academy", "Algorithms and Data Structures", "Computer Science", "CS-2026-A", "Egzamin", "4.5", None),
    ("kasia@fake.academy", "anna@fake.academy", "Algorithms and Data Structures", "Computer Science", "CS-2026-A", "Kolokwium", "4.0", None),
    ("kasia@fake.academy", "anna@fake.academy", "Algorithms and Data Structures", "Computer Science", "CS-2026-A", "Aktywność", "5.0", None),
    ("marek@fake.academy", "anna@fake.academy", "Algorithms and Data Structures", "Computer Science", "CS-2026-A", "Egzamin", "3.0", None),
    ("marek@fake.academy", "anna@fake.academy", "Algorithms and Data Structures", "Computer Science", "CS-2026-A", "Kolokwium", "3.5", None),
    ("kasia@fake.academy", "anna@fake.academy", "Databases", "Computer Science", "CS-2026-A", "Projekt", None, "ZAL"),
    ("ewa@fake.academy", "piotr@fake.academy", "Calculus", "Mathematics", "MATH-2026-A", "Egzamin", "4.0", None),
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


def _assignment_by_key(
    db: Session, teacher_email: str, subject_name: str, field_name: str, group_name: str
) -> TeachingAssignment:
    """Resolve a seed-referenced teaching assignment; fail loudly if missing."""
    teacher = _user_by_email(db, teacher_email)
    subject = _subject_by_name(db, subject_name)
    group = _group_by_name(db, field_name, group_name)
    assignment = db.scalar(
        sa.select(TeachingAssignment).where(
            TeachingAssignment.subject_id == subject.id,
            TeachingAssignment.teacher_id == teacher.id,
            TeachingAssignment.group_id == group.id,
        )
    )
    if assignment is None:
        raise SystemExit(
            f"seed references assignment {teacher_email} / {subject_name} /"
            f" {group_name}, but it does not exist"
        )
    return assignment


def _category_by_name(
    db: Session, assignment: TeachingAssignment, category_name: str
) -> GradeCategory:
    """Resolve a seed-referenced grade category; fail loudly if missing."""
    category = db.scalar(
        sa.select(GradeCategory).where(
            GradeCategory.assignment_id == assignment.id,
            GradeCategory.name == category_name,
        )
    )
    if category is None:
        raise SystemExit(
            f"seed references category {category_name!r} of assignment"
            f" {assignment.id}, but it does not exist"
        )
    return category



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


def seed_lesson_slots(db: Session) -> int:
    """Insert missing lesson slots; return how many were added."""
    inserted = 0
    print("Seeding lesson slots:")
    for (
        teacher_email,
        subject_name,
        field_name,
        group_name,
        day,
        start,
        end,
        room,
    ) in SEED_LESSON_SLOTS:
        assignment = _assignment_by_key(db, teacher_email, subject_name, field_name, group_name)
        start_time = datetime.time.fromisoformat(start)
        exists = db.scalar(
            sa.select(LessonSlot).where(
                LessonSlot.assignment_id == assignment.id,
                LessonSlot.day_of_week == day,
                LessonSlot.start_time == start_time,
            )
        )
        if exists is not None:
            print(f"  skip (already exists): {group_name:<12} {subject_name:<34} day={day} {start}")
            continue

        db.add(
            LessonSlot(
                assignment_id=assignment.id,
                day_of_week=day,
                start_time=start_time,
                end_time=datetime.time.fromisoformat(end),
                room=room,
            )
        )
        inserted += 1
        print(f"  add: {group_name:<12} {subject_name:<34} day={day} {start}-{end} {room}")
    return inserted


def seed_messages(db: Session) -> list[int]:
    """Insert missing messages; return the seeded message ids in list order."""
    ids: list[int] = []
    print("Seeding messages:")
    for sender_email, recipient, title, content, minutes_ago in SEED_MESSAGES:
        sender = _user_by_email(db, sender_email)
        # Recipient: a person (email string) or a group ((field, name) pair).
        if isinstance(recipient, str):
            recipient_user = _user_by_email(db, recipient)
            recipient_id = recipient_user.id
            group_id = None
        else:
            field_name, group_name = recipient
            group = _group_by_name(db, field_name, group_name)
            recipient_id = None
            group_id = group.id
        exists = db.scalar(
            sa.select(Message).where(
                Message.sender_id == sender.id,
                Message.recipient_id == recipient_id,
                Message.group_id == group_id,
                # title is None for chat messages — compare with IS NULL.
                Message.title.is_(None) if title is None else Message.title == title,
            )
        )
        if exists is not None:
            print(f"  skip (already exists): {title or content.splitlines()[0]}")
            ids.append(exists.id)
            continue

        message = Message(
            sender_id=sender.id,
            recipient_id=recipient_id,
            group_id=group_id,
            title=title,
            content=content,
            # Explicit timestamp: now() would give the whole seed run ONE
            # shared created_at (transaction start), putting the reply
            # before the question once ids tie-break the sort.
            created_at=datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(minutes=minutes_ago),
        )
        db.add(message)
        db.flush()  # make the fresh id visible for the receipt step
        ids.append(message.id)
        target = recipient if isinstance(recipient, str) else f"{recipient[1]} (group)"
        print(f"  add: {sender_email} -> {target}: {title or content.splitlines()[0]}")
    return ids


def seed_message_reads(db: Session, message_ids: list[int]) -> int:
    """Insert missing read receipts; return how many were added."""
    inserted = 0
    print("Seeding message read receipts:")
    for reader_email, index in SEED_MESSAGE_READS:
        reader = _user_by_email(db, reader_email)
        message_id = message_ids[index]
        exists = db.scalar(
            sa.select(MessageReadStatus).where(
                MessageReadStatus.message_id == message_id,
                MessageReadStatus.user_id == reader.id,
            )
        )
        if exists is not None:
            print(f"  skip (already exists): {reader_email} / message {message_id}")
            continue

        db.add(
            MessageReadStatus(
                message_id=message_id,
                user_id=reader.id,
                read_at=datetime.datetime.now(datetime.timezone.utc),
            )
        )
        inserted += 1
        print(f"  add: {reader_email} read message {message_id}")
    return inserted


def seed_grade_categories(db: Session) -> int:
    """Insert missing grade categories; return how many were added."""
    inserted = 0
    print("Seeding grade categories:")
    for teacher_email, subject_name, field_name, group_name, name, weight in SEED_GRADE_CATEGORIES:
        assignment = _assignment_by_key(db, teacher_email, subject_name, field_name, group_name)
        exists = db.scalar(
            sa.select(GradeCategory).where(
                GradeCategory.assignment_id == assignment.id,
                GradeCategory.name == name,
            )
        )
        if exists is not None:
            print(f"  skip (already exists): {group_name:<12} {subject_name} / {name}")
            continue

        db.add(
            GradeCategory(
                assignment_id=assignment.id,
                name=name,
                weight=decimal.Decimal(weight),
            )
        )
        inserted += 1
        print(f"  add: {group_name:<12} {subject_name:<34} {name} ({weight}%)")
    return inserted


def seed_grades(db: Session) -> int:
    """Insert missing sample grades; return how many were added."""
    inserted = 0
    print("Seeding grades:")
    for (
        student_email,
        teacher_email,
        subject_name,
        field_name,
        group_name,
        category_name,
        value,
        symbol,
    ) in SEED_GRADES:
        student = _user_by_email(db, student_email)
        assignment = _assignment_by_key(db, teacher_email, subject_name, field_name, group_name)
        category = _category_by_name(db, assignment, category_name)
        exists = db.scalar(
            sa.select(Grade).where(
                Grade.student_id == student.id,
                Grade.category_id == category.id,
            )
        )
        if exists is not None:
            print(f"  skip (already exists): {student_email} / {subject_name} / {category_name}")
            continue

        db.add(
            Grade(
                student_id=student.id,
                category_id=category.id,
                value=decimal.Decimal(value) if value is not None else None,
                symbol=symbol,
            )
        )
        inserted += 1
        outcome = symbol if symbol is not None else value
        print(f"  add: {student_email:<22} {subject_name:<34} {category_name} = {outcome}")
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
        db.flush()
        inserted += seed_lesson_slots(db)
        db.flush()
        inserted += seed_grade_categories(db)
        db.flush()
        inserted += seed_grades(db)
        db.flush()
        message_ids = seed_messages(db)
        db.flush()
        inserted += seed_message_reads(db, message_ids)

        # One commit at the end: either all inserts succeed or none.
        db.commit()

        expected = (
            len(SEED_USERS)
            + len(SEED_FIELDS)
            + len(SEED_GROUPS)
            + len(SEED_SUBJECTS)
            + len(SEED_TEACHING_ASSIGNMENTS)
            + len(SEED_GROUP_MEMBERSHIPS)
            + len(SEED_LESSON_SLOTS)
            + len(SEED_GRADE_CATEGORIES)
            + len(SEED_GRADES)
            + len(SEED_MESSAGES)
        )
        print(f"Done: {inserted} inserted, {expected - inserted} skipped.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
