"""Add journal tables

Revision ID: 002_journal_tables
Revises: 001_initial_schema
Create Date: 2026-01-08 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '002_journal_tables'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Create daily_journals table
    op.create_table(
        'daily_journals',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('date', sa.Date, nullable=False, unique=True),
        sa.Column('morning_intention', sa.Text, default=''),
        sa.Column('end_of_day_reflection', sa.Text, default=''),
        sa.Column('energy_level', sa.Integer, default=3),
        sa.Column('mood', sa.String(50), default=''),
        sa.Column('wins', sa.JSON, default=list),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create work_sessions table
    op.create_table(
        'work_sessions',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('journal_id', sa.String(50), sa.ForeignKey('daily_journals.id', ondelete='CASCADE')),
        sa.Column('start_time', sa.DateTime, nullable=False),
        sa.Column('end_time', sa.DateTime, nullable=True),
        sa.Column('task', sa.String(500), nullable=False),
        sa.Column('files_touched', sa.JSON, default=list),
        sa.Column('decisions_made', sa.JSON, default=list),
        sa.Column('notes', sa.Text, default=''),
        sa.Column('learnings', sa.JSON, default=list),
        sa.Column('challenges', sa.JSON, default=list),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    
    # Create session_reflections table
    op.create_table(
        'session_reflections',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('session_id', sa.String(50), sa.ForeignKey('work_sessions.id', ondelete='CASCADE')),
        sa.Column('reflection_text', sa.Text, nullable=False),
        sa.Column('key_insights', sa.JSON, default=list),
        sa.Column('related_memories', sa.JSON, default=list),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('idx_journals_date', 'daily_journals', ['date'])
    op.create_index('idx_sessions_journal', 'work_sessions', ['journal_id'])
    op.create_index('idx_sessions_start', 'work_sessions', ['start_time'])
    op.create_index('idx_reflections_session', 'session_reflections', ['session_id'])


def downgrade():
    op.drop_index('idx_reflections_session', table_name='session_reflections')
    op.drop_index('idx_sessions_start', table_name='work_sessions')
    op.drop_index('idx_sessions_journal', table_name='work_sessions')
    op.drop_index('idx_journals_date', table_name='daily_journals')
    
    op.drop_table('session_reflections')
    op.drop_table('work_sessions')
    op.drop_table('daily_journals')
