"""add ix_links_owner_created_code

Revision ID: 33545d81c567
Revises: 7749525392cd
Create Date: 2026-11-14 15:20:53.246636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33545d81c567'
down_revision: Union[str, Sequence[str], None] = '7749525392cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
    "ix_links_owner_created_code",
    "links",
    ["owner_id", sa.text("created_at DESC"), sa.text("code DESC")],
    )



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_links_owner_created_code", table_name="links")
