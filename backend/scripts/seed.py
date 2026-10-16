"""Seed the database with development users: every role, plus one
DEACTIVATED student (to test the 403 path of POST /auth/login).

Usage (from the backend/ directory, with the docker compose db running):

    PowerShell:
        $env:DATABASE_URL = "postgresql+psycopg://dev:dev@localhost:5432/dev"
        $env:JWT_SECRET   = "<same value as .env>"
        python scripts/seed.py

Idempotent: users are matched by email and existing ones are skipped,
so it is safe to run again at any time.

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

from app.database import SessionLocal  # noqa: E402
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


def main() -> None:
    """Insert any seed users that are missing; skip existing ones."""
    db = SessionLocal()
    inserted = 0
    try:
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

        # One commit at the end: either all inserts succeed or none.
        db.commit()
        print(f"Done: {inserted} inserted, {len(SEED_USERS) - inserted} skipped.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
