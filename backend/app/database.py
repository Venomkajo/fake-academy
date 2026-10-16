import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]

# Shared connection pool; pre_ping quietly replaces dead connections.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
# Session factory — each request gets its own session via get_db().
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# Parent of every ORM model; Alembic autogenerate reads its metadata.
class Base(DeclarativeBase):
    pass


# Function to get a database session for dependency injection in FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()