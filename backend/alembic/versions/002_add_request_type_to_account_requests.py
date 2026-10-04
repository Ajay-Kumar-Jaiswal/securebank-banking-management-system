"""Add request_type to account_closure_requests

Revision ID: 002_request_type
Revises: 001_initial_schema
Create Date: 2026-10-03 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_request_type'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'account_closure_requests',
        sa.Column('request_type', sa.String(length=20), server_default='CLOSURE', nullable=False)
    )
    op.create_index('idx_closure_request_type', 'account_closure_requests', ['request_type'])


def downgrade() -> None:
    op.drop_index('idx_closure_request_type', table_name='account_closure_requests')
    op.drop_column('account_closure_requests', 'request_type')
