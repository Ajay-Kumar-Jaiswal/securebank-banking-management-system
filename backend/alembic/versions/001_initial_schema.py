"""Initial database schema migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-02 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def pk_type():
    return sa.BigInteger().with_variant(sa.Integer, 'sqlite')


def fk_type():
    return sa.BigInteger().with_variant(sa.Integer, 'sqlite')


def upgrade() -> None:
    # users
    op.create_table(
        'users',
        sa.Column('user_id', pk_type(), autoincrement=True, nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=150), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=20), server_default='CUSTOMER', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email', name='uk_users_email'),
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)

    # accounts
    op.create_table(
        'accounts',
        sa.Column('account_id', pk_type(), autoincrement=True, nullable=False),
        sa.Column('account_number', sa.String(length=20), nullable=False),
        sa.Column('user_id', fk_type(), nullable=False),
        sa.Column('account_type', sa.String(length=20), nullable=False),
        sa.Column('balance', sa.Numeric(precision=19, scale=2), server_default='0.00', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('version', sa.BigInteger(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name='fk_accounts_user'),
        sa.PrimaryKeyConstraint('account_id'),
        sa.UniqueConstraint('account_number', name='uk_accounts_account_number'),
    )
    op.create_index('idx_accounts_user_id', 'accounts', ['user_id'])
    op.create_index('idx_accounts_account_number', 'accounts', ['account_number'], unique=True)

    # transactions
    op.create_table(
        'transactions',
        sa.Column('transaction_id', pk_type(), autoincrement=True, nullable=False),
        sa.Column('transaction_reference', sa.String(length=40), nullable=False),
        sa.Column('account_id', fk_type(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=19, scale=2), nullable=False),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('balance_before', sa.Numeric(precision=19, scale=2), nullable=True),
        sa.Column('balance_after', sa.Numeric(precision=19, scale=2), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='SUCCESS', nullable=False),
        sa.Column('related_account_id', fk_type(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.account_id'], name='fk_transactions_account'),
        sa.ForeignKeyConstraint(['related_account_id'], ['accounts.account_id'], name='fk_transactions_related_account'),
        sa.PrimaryKeyConstraint('transaction_id'),
    )
    op.create_index('idx_transactions_account_id', 'transactions', ['account_id'])
    op.create_index('idx_transactions_reference', 'transactions', ['transaction_reference'])
    op.create_index('idx_transactions_created_at', 'transactions', ['created_at'])

    # beneficiaries
    op.create_table(
        'beneficiaries',
        sa.Column('beneficiary_id', pk_type(), autoincrement=True, nullable=False),
        sa.Column('user_id', fk_type(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('account_number', sa.String(length=20), nullable=False),
        sa.Column('bank_name', sa.String(length=150), nullable=False),
        sa.Column('ifsc_code', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name='fk_beneficiaries_user'),
        sa.PrimaryKeyConstraint('beneficiary_id'),
    )
    op.create_index('idx_beneficiaries_user_id', 'beneficiaries', ['user_id'])

    # account_closure_requests
    op.create_table(
        'account_closure_requests',
        sa.Column('closure_request_id', pk_type(), autoincrement=True, nullable=False),
        sa.Column('user_id', fk_type(), nullable=False),
        sa.Column('account_id', fk_type(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('additional_notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='PENDING', nullable=False),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('reviewed_by', fk_type(), nullable=True),
        sa.Column('requested_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name='fk_closure_user'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.account_id'], name='fk_closure_account'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.user_id'], name='fk_closure_reviewer'),
        sa.PrimaryKeyConstraint('closure_request_id'),
    )
    op.create_index('idx_closure_user_id', 'account_closure_requests', ['user_id'])
    op.create_index('idx_closure_account_id', 'account_closure_requests', ['account_id'])
    op.create_index('idx_closure_status', 'account_closure_requests', ['status'])

    # audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('audit_id', pk_type(), autoincrement=True, nullable=False),
        sa.Column('actor_user_id', fk_type(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.user_id'], name='fk_audit_actor'),
        sa.PrimaryKeyConstraint('audit_id'),
    )
    op.create_index('idx_audit_actor_id', 'audit_logs', ['actor_user_id'])
    op.create_index('idx_audit_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_timestamp', 'audit_logs', ['timestamp'])

    # email_logs
    op.create_table(
        'email_logs',
        sa.Column('email_log_id', pk_type(), autoincrement=True, nullable=False),
        sa.Column('recipient_email', sa.String(length=150), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='SENT', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('email_log_id'),
    )
    op.create_index('idx_email_recipient', 'email_logs', ['recipient_email'])
    op.create_index('idx_email_created_at', 'email_logs', ['created_at'])


def downgrade() -> None:
    op.drop_table('email_logs')
    op.drop_table('audit_logs')
    op.drop_table('account_closure_requests')
    op.drop_table('beneficiaries')
    op.drop_table('transactions')
    op.drop_table('accounts')
    op.drop_table('users')
