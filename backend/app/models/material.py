"""Material ORM model."""

import datetime

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Material(Base):
    """One row per uploaded file attached to a subject (the file body itself lives in MinIO/S3 storage)."""

    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # Subject this file belongs to. Indexed because Postgres does NOT
    # auto-index FK columns, and "materials for subject X" filters on it.
    subject_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("subjects.id"), index=True
    )
    # Uploader's account — users.id doubles as the teacher id. Indexed for
    # "files uploaded by user Y".
    uploaded_by: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id"), index=True
    )
    # Original file name as the uploader's browser reported it — shown to
    # downloading users.
    file_name: Mapped[str] = mapped_column(sa.String(255))
    # Object key (path) of the file in MinIO — the DB row never stores the
    # file body, only the pointer into the S3-compatible storage. One row
    # per stored object, hence unique; 1024 chars is the S3 key limit.
    s3_key: Mapped[str] = mapped_column(sa.String(1024), unique=True)
    # MIME type of the stored file, e.g. "application/pdf".
    mime_type: Mapped[str] = mapped_column(sa.String(255))
    # Size of the stored object in bytes — bigint, because files may well
    # exceed the ~2 GB ceiling of a plain int.
    size_bytes: Mapped[int] = mapped_column(sa.BigInteger)
    # Filled in by the database on insert.
    uploaded_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(),
    )