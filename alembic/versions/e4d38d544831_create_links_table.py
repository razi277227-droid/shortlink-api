"""create links table

Revision ID: e4d38d544831
Revises: 
Create Date: 2026-10-11 19:15:54.191762

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4d38d544831'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "links",
        sa.Column("code", sa.Text(), primary_key = True, nullable = False),
            sa.Column("original_url", sa.Text(), nullable = False),
            sa.Column("clicks", sa.BigInteger, nullable = False, server_default = sa.text("0")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable = False, server_default = sa.text("now()")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("links")
    pass
