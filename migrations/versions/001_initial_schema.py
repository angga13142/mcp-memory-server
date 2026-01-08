"""Initial schema migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-01-08 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import JSON

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema."""
    # Project brief table
    op.create_table(
        'project_brief',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True, default=''),
        sa.Column('goals', JSON, nullable=True, default=list),
        sa.Column('version', sa.String(length=50), nullable=True, default='1.0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Tech stack table
    op.create_table(
        'tech_stack',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('languages', JSON, nullable=True, default=list),
        sa.Column('frameworks', JSON, nullable=True, default=list),
        sa.Column('tools', JSON, nullable=True, default=list),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Decisions table
    op.create_table(
        'decisions',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('decision', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True, default=''),
        sa.Column('alternatives_considered', JSON, nullable=True, default=list),
        sa.Column('consequences', JSON, nullable=True, default=list),
        sa.Column('tags', JSON, nullable=True, default=list),
        sa.Column('status', sa.String(length=50), nullable=True, default='accepted'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True, default='user'),
        sa.Column('superseded_by', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Active context table
    op.create_table(
        'active_context',
        sa.Column('id', sa.Integer(), nullable=False, default=1),
        sa.Column('current_task', sa.Text(), nullable=True, default=''),
        sa.Column('related_files', JSON, nullable=True, default=list),
        sa.Column('relevant_decisions', JSON, nullable=True, default=list),
        sa.Column('notes', sa.Text(), nullable=True, default=''),
        sa.Column('working_branch', sa.String(length=255), nullable=True, default=''),
        sa.Column('session_id', sa.String(length=100), nullable=True, default=''),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint('id')
    )

    # Tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True, default=''),
        sa.Column('status', sa.String(length=50), nullable=True, default='next'),
        sa.Column('priority', sa.String(length=50), nullable=True, default='medium'),
        sa.Column('tags', JSON, nullable=True, default=list),
        sa.Column('parent_id', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('blocked_reason', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Memory entries table
    op.create_table(
        'memory_entries',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=True, default='note'),
        sa.Column('source_id', sa.String(length=50), nullable=True),
        sa.Column('entry_metadata', JSON, nullable=True, default=dict),
        sa.Column('tags', JSON, nullable=True, default=list),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # System patterns table
    op.create_table(
        'system_patterns',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True, default=''),
        sa.Column('example', sa.Text(), nullable=True, default=''),
        sa.Column('tags', JSON, nullable=True, default=list),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('system_patterns')
    op.drop_table('memory_entries')
    op.drop_table('tasks')
    op.drop_table('active_context')
    op.drop_table('decisions')
    op.drop_table('tech_stack')
    op.drop_table('project_brief')
