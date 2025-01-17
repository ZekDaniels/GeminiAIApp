"""Initial

Revision ID: f0f33c7efa6a
Revises: 
Create Date: 2024-12-10 16:11:51.831294

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0f33c7efa6a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('integrations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('page_count', sa.Integer(), nullable=False),
    sa.Column('processing_status', sa.Enum('PROCESSED', 'PENDING', 'FAILED', name='processingstatus'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_integrations_filename'), 'integrations', ['filename'], unique=False)
    op.create_index(op.f('ix_integrations_id'), 'integrations', ['id'], unique=False)
    op.create_table('conversation_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('integration_id', sa.Integer(), nullable=False),
    sa.Column('user_query', sa.Text(), nullable=False),
    sa.Column('assistant_response', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_history_id'), 'conversation_history', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_conversation_history_id'), table_name='conversation_history')
    op.drop_table('conversation_history')
    op.drop_index(op.f('ix_integrations_id'), table_name='integrations')
    op.drop_index(op.f('ix_integrations_filename'), table_name='integrations')
    op.drop_table('integrations')
    # ### end Alembic commands ###
