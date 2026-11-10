"""create_initial_tables

Revision ID: f41f14003d54
Revises: 
Create Date: 2026-11-10 12:59:26.907423

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f41f14003d54'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create the 6 core FeelConnect tables."""
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_name'), 'users', ['name'], unique=False)

    # 2. conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('person_a_id', sa.Integer(), nullable=False),
        sa.Column('person_b_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['person_a_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['person_b_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_conversations_person_a_id'), 'conversations', ['person_a_id'], unique=False)
    op.create_index(op.f('ix_conversations_person_b_id'), 'conversations', ['person_b_id'], unique=False)

    # 3. messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('emotion', sa.String(length=64), server_default='neutral', nullable=False),
        sa.Column('emotion_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_messages_sender_id'), 'messages', ['sender_id'], unique=False)
    op.create_index(op.f('ix_messages_timestamp'), 'messages', ['timestamp'], unique=False)

    # 4. daily_relationship_metrics table
    op.create_table(
        'daily_relationship_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('positive_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('negative_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('affection_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('message_count', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_daily_relationship_metrics_conversation_id'), 'daily_relationship_metrics', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_daily_relationship_metrics_date'), 'daily_relationship_metrics', ['date'], unique=False)

    # 5. relationship_stages table (1-to-1 relationship with unique constraint)
    op.create_table(
        'relationship_stages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('stage', sa.String(length=32), server_default='stranger', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conversation_id'),
    )
    op.create_index(op.f('ix_relationship_stages_conversation_id'), 'relationship_stages', ['conversation_id'], unique=True)

    # 6. analysis_records table
    op.create_table(
        'analysis_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('analysis_type', sa.String(length=32), server_default='chat', nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_analysis_records_conversation_id'), 'analysis_records', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_analysis_records_created_at'), 'analysis_records', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema: Drop tables in reverse topological order."""
    op.drop_table('analysis_records')
    op.drop_table('relationship_stages')
    op.drop_table('daily_relationship_metrics')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('users')
