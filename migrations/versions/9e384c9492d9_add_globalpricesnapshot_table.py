"""Add GlobalPriceSnapshot table

Revision ID: 9e384c9492d9
Revises: a3f1e8b20d4c
Create Date: 2026-04-23 10:07:42.578761

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e384c9492d9'
down_revision = 'a3f1e8b20d4c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('global_price_snapshot',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_key', sa.String(length=200), nullable=False),
        sa.Column('product_name', sa.String(length=500), nullable=True),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('global_price_snapshot', schema=None) as batch_op:
        batch_op.create_index('ix_gps_product_key', ['product_key'], unique=False)
        batch_op.create_index('ix_gps_key_platform', ['product_key', 'platform'], unique=False)


def downgrade():
    with op.batch_alter_table('global_price_snapshot', schema=None) as batch_op:
        batch_op.drop_index('ix_gps_key_platform')
        batch_op.drop_index('ix_gps_product_key')

    op.drop_table('global_price_snapshot')
