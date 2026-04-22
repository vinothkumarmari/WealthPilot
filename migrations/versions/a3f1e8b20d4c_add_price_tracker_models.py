"""Add TrackedProduct and PriceHistory models

Revision ID: a3f1e8b20d4c
Revises: 2698ff9ef00c
Create Date: 2026-04-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3f1e8b20d4c'
down_revision = '2698ff9ef00c'
branch_labels = None
depends_on = None


def upgrade():
    # Add enable_price_tracker column to user table
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('enable_price_tracker', sa.Boolean(), server_default='1', nullable=True))

    op.create_table('tracked_product',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=True),
        sa.Column('name', sa.String(length=500), nullable=True),
        sa.Column('image_url', sa.String(length=2048), nullable=True),
        sa.Column('current_price', sa.Float(), nullable=True),
        sa.Column('min_price', sa.Float(), nullable=True),
        sa.Column('max_price', sa.Float(), nullable=True),
        sa.Column('target_price', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_checked', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tracked_user', 'tracked_product', ['user_id'])

    op.create_table('price_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['tracked_product.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pricehist_product', 'price_history', ['product_id'])


def downgrade():
    op.drop_index('ix_pricehist_product', table_name='price_history')
    op.drop_table('price_history')
    op.drop_index('ix_tracked_user', table_name='tracked_product')
    op.drop_table('tracked_product')
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('enable_price_tracker')
