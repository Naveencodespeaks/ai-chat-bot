"""create tickets table

Revision ID: b1c2d3f4e567
Revises: 39ed6b2ef049
Create Date: 2026-02-14 12:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3f4e567'
down_revision: Union[str, Sequence[str], None] = '39ed6b2ef049'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tickets table"""
    op.create_table(
        'tickets',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('assigned_agent_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, index=True),
        sa.Column('priority', sa.String(length=50), nullable=True, index=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('sla_due_at', sa.DateTime(), nullable=True),
        sa.Column('first_response_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('sla_breached', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('escalation_level', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('reassigned_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('routing_method', sa.String(length=20), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('ai_predicted_department', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Drop tickets table"""
    op.drop_table('tickets')
