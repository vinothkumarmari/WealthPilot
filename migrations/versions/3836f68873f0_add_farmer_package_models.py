"""add farmer package models

Revision ID: 3836f68873f0
Revises: fe358f44541a
Create Date: 2026-07-13 16:55:15.145105

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3836f68873f0'
down_revision = 'fe358f44541a'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'farmer_profile' not in existing_tables:
        op.create_table('farmer_profile',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('location_name', sa.String(length=150), nullable=True),
            sa.Column('district', sa.String(length=100), nullable=True),
            sa.Column('state_name', sa.String(length=100), nullable=True),
            sa.Column('land_size_acres', sa.Float(), nullable=True),
            sa.Column('irrigation_type', sa.String(length=50), nullable=True),
            sa.Column('soil_type', sa.String(length=50), nullable=True),
            sa.Column('main_crop', sa.String(length=100), nullable=True),
            sa.Column('annual_farm_income', sa.Float(), nullable=True),
            sa.Column('annual_household_income', sa.Float(), nullable=True),
            sa.Column('available_cash', sa.Float(), nullable=True),
            sa.Column('available_credit', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['user.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id')
        )
    if 'ix_farmer_profile_user' not in {idx['name'] for idx in inspector.get_indexes('farmer_profile')}:
        op.create_index('ix_farmer_profile_user', 'farmer_profile', ['user_id'], unique=False)

    if 'farmer_log' not in existing_tables:
        op.create_table('farmer_log',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('entry_type', sa.String(length=30), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=False),
            sa.Column('amount', sa.Float(), nullable=True),
            sa.Column('quantity', sa.Float(), nullable=True),
            sa.Column('notes', sa.String(length=400), nullable=True),
            sa.Column('entry_date', sa.Date(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['user.id']),
            sa.PrimaryKeyConstraint('id')
        )
    if 'ix_farmer_log_user_date' not in {idx['name'] for idx in inspector.get_indexes('farmer_log')}:
        op.create_index('ix_farmer_log_user_date', 'farmer_log', ['user_id', 'entry_date'], unique=False)

    if 'farmer_season_plan' not in existing_tables:
        op.create_table('farmer_season_plan',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('crop_name', sa.String(length=100), nullable=False),
            sa.Column('season_name', sa.String(length=50), nullable=True),
            sa.Column('acreage', sa.Float(), nullable=True),
            sa.Column('sowing_date', sa.Date(), nullable=True),
            sa.Column('expected_yield', sa.Float(), nullable=True),
            sa.Column('expected_price', sa.Float(), nullable=True),
            sa.Column('seed_cost', sa.Float(), nullable=True),
            sa.Column('fertilizer_cost', sa.Float(), nullable=True),
            sa.Column('pesticide_cost', sa.Float(), nullable=True),
            sa.Column('labor_cost', sa.Float(), nullable=True),
            sa.Column('irrigation_cost', sa.Float(), nullable=True),
            sa.Column('machinery_cost', sa.Float(), nullable=True),
            sa.Column('transport_cost', sa.Float(), nullable=True),
            sa.Column('interest_cost', sa.Float(), nullable=True),
            sa.Column('misc_cost', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['user.id']),
            sa.PrimaryKeyConstraint('id')
        )
    if 'ix_farmer_plan_user_date' not in {idx['name'] for idx in inspector.get_indexes('farmer_season_plan')}:
        op.create_index('ix_farmer_plan_user_date', 'farmer_season_plan', ['user_id', 'created_at'], unique=False)


def downgrade():
    op.drop_index('ix_farmer_plan_user_date', table_name='farmer_season_plan')
    op.drop_table('farmer_season_plan')
    op.drop_index('ix_farmer_log_user_date', table_name='farmer_log')
    op.drop_table('farmer_log')
    op.drop_index('ix_farmer_profile_user', table_name='farmer_profile')
    op.drop_table('farmer_profile')
