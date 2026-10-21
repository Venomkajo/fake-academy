import datetime

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# SQLAlchemy model for the RefreshToken table
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    # Owning account — a refresh token always belongs to exactly one user.
    # Indexed because Postgres does NOT auto-index FK columns, and common
    # queries ("list/revoke every session of user X") filter on user_id.
    user_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id"), index=True
    )
    # SHA-256 hex digest of the raw refresh token (64 characters). Only the
    # hash is stored — the plaintext token lives solely in the client's
    # hands, so a leaked database cannot be replayed against the API.
    token_hash: Mapped[str] = mapped_column(sa.String(255), unique=True)
    # Moment the token stops being valid even if it was never revoked;
    # timezone-aware so it compares cleanly against UTC "now".
    expires_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True))
    # Soft kill switch: flipped when the token is traded for a new one
    # (rotation) or when the user logs out / gets all sessions revoked.
    # Rows are never deleted, keeping an audit trail of issued tokens.
    revoked: Mapped[bool] = mapped_column(
        sa.Boolean, default=False, server_default=sa.sql.expression.false()
    )
