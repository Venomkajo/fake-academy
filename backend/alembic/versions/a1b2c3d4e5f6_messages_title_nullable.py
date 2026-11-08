"""messages title nullable

Revision ID: a1b2c3d4e5f6
Revises: e7568ce92c08
Create Date: 2026-11-08 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'e7568ce92c08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Private chat messages carry no title (announcements keep theirs);
    # the column must be nullable for that.
    op.alter_column('messages', 'title', existing_type=sa.String(length=255), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # NULL titles would violate the NOT NULL constraint — fill them first.
    op.execute("UPDATE messages SET title = '(bez tytułu)' WHERE title IS NULL")
    op.alter_column('messages', 'title', existing_type=sa.String(length=255), nullable=False)