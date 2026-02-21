from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'ff6445046335'
down_revision = 'cada0755b062'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # 1️⃣ Create ENUM
    conversation_status_enum = postgresql.ENUM(
        'OPEN', 'CLOSED', 'ESCALATED',
        name='conversation_status'
    )
    conversation_status_enum.create(bind, checkfirst=True)

    # 2️⃣ Add columns
    op.add_column(
        'conversations',
        sa.Column(
            'status',
            conversation_status_enum,
            nullable=False,
            server_default='OPEN'
        )
    )

    op.add_column(
        'conversations',
        sa.Column('channel', sa.String(50),
                  nullable=False,
                  server_default='WHATSAPP')
    )

    op.add_column(
        'conversations',
        sa.Column('last_message_at', sa.DateTime(), nullable=True)
    )

    op.add_column(
        'conversations',
        sa.Column('created_at',
                  sa.DateTime(timezone=True),
                  server_default=sa.text('now()'),
                  nullable=False)
    )

    op.add_column(
        'conversations',
        sa.Column('updated_at',
                  sa.DateTime(timezone=True),
                  server_default=sa.text('now()'),
                  nullable=False)
    )

    # 🔥 remove default after migration
    op.alter_column('conversations', 'status', server_default=None)

    # 3️⃣ Indexes
    op.create_index('idx_conversation_owner', 'conversations', ['owner_id'])
    op.create_index('idx_conversation_assigned', 'conversations', ['assigned_user_id'])
    op.create_index('idx_conversation_status', 'conversations', ['status'])
    op.create_index('idx_conversation_last_message', 'conversations', ['last_message_at'])

    op.create_index('idx_tickets_assigned_agent_id', 'tickets', ['assigned_agent_id'])
    op.create_index('idx_tickets_conversation_id', 'tickets', ['conversation_id'])
    op.create_index('idx_tickets_created_by_id', 'tickets', ['created_by_id'])
    op.create_index('idx_tickets_department_id', 'tickets', ['department_id'])
    op.create_index('idx_tickets_priority', 'tickets', ['priority'])
    op.create_index('idx_tickets_status', 'tickets', ['status'])
def downgrade() -> None:
    """Downgrade schema."""

    bind = op.get_bind()

    # Drop indexes
    op.drop_index('idx_tickets_status', table_name='tickets')
    op.drop_index('idx_tickets_priority', table_name='tickets')
    op.drop_index('idx_tickets_department_id', table_name='tickets')
    op.drop_index('idx_tickets_created_by_id', table_name='tickets')
    op.drop_index('idx_tickets_conversation_id', table_name='tickets')
    op.drop_index('idx_tickets_assigned_agent_id', table_name='tickets')

    op.drop_index('idx_conversation_last_message', table_name='conversations')
    op.drop_index('idx_conversation_status', table_name='conversations')
    op.drop_index('idx_conversation_assigned', table_name='conversations')
    op.drop_index('idx_conversation_owner', table_name='conversations')

    # Drop columns
    op.drop_column('conversations', 'updated_at')
    op.drop_column('conversations', 'created_at')
    op.drop_column('conversations', 'last_message_at')
    op.drop_column('conversations', 'channel')
    op.drop_column('conversations', 'status')

    # Drop ENUM
    conversation_status_enum = postgresql.ENUM(
        'OPEN', 'CLOSED', 'ESCALATED',
        name='conversation_status'
    )
    conversation_status_enum.drop(bind, checkfirst=True)