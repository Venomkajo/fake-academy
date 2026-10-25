"""Database setup: the engine, the session factory and the ORM base."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]

# Shared connection pool; pre_ping quietly replaces dead connections.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
# Session factory — each request gets its own session via get_db().
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Parent of every ORM model; Alembic autogenerate reads its metadata."""


def get_db():
    """Yield one database session per request (FastAPI dependency injection)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()