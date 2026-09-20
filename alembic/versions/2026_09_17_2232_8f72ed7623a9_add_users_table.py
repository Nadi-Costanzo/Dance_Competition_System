"""Add users table.

Revision ID: 8f72ed7623a9
Revises: 2cdb0a6662ca
Create Date: 2026-09-17 22:32:12.995396+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '8f72ed7623a9'
down_revision: str | Sequence[str] | None = '2cdb0a6662ca'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('surname', sa.String(length=30), nullable=False),
        sa.Column('name', sa.String(length=30), nullable=False),
        sa.Column('patronymic', sa.String(length=30), nullable=True),
        sa.Column(
            'role', sa.String(length=10), server_default='user', nullable=False
        ),
        sa.Column(
            'is_certified_judge',
            sa.Boolean(),
            server_default=sa.text('0'),
            nullable=False,
        ),
        sa.Column('judge_category', sa.String(length=20), nullable=True),
        sa.Column(
            'token_version',
            sa.Integer(),
            server_default=sa.text('0'),
            nullable=False,
        ),
        sa.Column(
            'sync_origin',
            sa.String(length=10),
            server_default='local',
            nullable=False,
        ),
        sa.Column(
            'is_active',
            sa.Boolean(),
            server_default=sa.text('1'),
            nullable=False,
        ),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.CheckConstraint(
            "judge_category IN ('mass_sport', 'youth', "
            "'third', 'second', 'first', 'all_russian')",
            name=op.f('ck_users_valid_judge_category'),
        ),
        sa.CheckConstraint(
            "role IN ('admin', 'user')", name=op.f('ck_users_valid_role')
        ),
        sa.CheckConstraint(
            "sync_origin IN ('local', 'cloud')",
            name=op.f('ck_users_valid_sync_origin'),
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('email', name=op.f('uq_users_email')),
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_users_name'), ['name'], unique=False
        )
        batch_op.create_index(
            batch_op.f('ix_users_surname'), ['surname'], unique=False
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_surname'))
        batch_op.drop_index(batch_op.f('ix_users_name'))

    op.drop_table('users')
