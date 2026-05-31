"""Add enable_sms_sync and sms_sync_token to User

Revision ID: b7e2a1f39c5d
Revises: fe358f44541a
Create Date: 2026-05-31 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b7e2a1f39c5d'
down_revision = 'fe358f44541a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('enable_sms_sync', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('sms_sync_token', sa.String(length=64), nullable=True))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('sms_sync_token')
        batch_op.drop_column('enable_sms_sync')
