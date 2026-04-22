"""Add GoldPriceAlert model

Revision ID: 2698ff9ef00c
Revises: 
Create Date: 2026-04-22 21:43:50.558645

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2698ff9ef00c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('gold_price_alert',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('karat', sa.String(length=10), nullable=True),
        sa.Column('direction', sa.String(length=10), nullable=False),
        sa.Column('target_price', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('triggered', sa.Boolean(), nullable=True),
        sa.Column('triggered_at', sa.DateTime(), nullable=True),
        sa.Column('triggered_price', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('gold_price_alert', schema=None) as batch_op:
        batch_op.create_index('ix_goldalert_user', ['user_id'], unique=False)


def downgrade():
    with op.batch_alter_table('gold_price_alert', schema=None) as batch_op:
        batch_op.drop_index('ix_goldalert_user')
    op.drop_table('gold_price_alert')
