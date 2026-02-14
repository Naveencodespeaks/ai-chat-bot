"""add ticket fields

Revision ID: a4f1d2b3c6e7
Revises: 39ed6b2ef049
Create Date: 2026-02-14 11:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4f1d2b3c6e7'
down_revision: Union[str, Sequence[str], None] = 'b1c2d3f4e567'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op migration; tickets table created in earlier migration."""
    pass


def downgrade() -> None:
    """No-op downgrade."""
    pass
