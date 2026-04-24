"""Add gamification models UserStreak and UserBadge

Revision ID: 9e570c8725cb
Revises: 9e384c9492d9
Create Date: 2026-04-24 12:01:05.151296

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e570c8725cb'
down_revision = '9e384c9492d9'
branch_labels = None
depends_on = None


def upgrade():
    # Create gamification tables
    op.create_table('user_streak',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('expense_streak', sa.Integer(), server_default='0'),
        sa.Column('login_streak', sa.Integer(), server_default='0'),
        sa.Column('budget_streak', sa.Integer(), server_default='0'),
        sa.Column('best_expense_streak', sa.Integer(), server_default='0'),
        sa.Column('best_login_streak', sa.Integer(), server_default='0'),
        sa.Column('last_expense_date', sa.Date(), nullable=True),
        sa.Column('last_login_date', sa.Date(), nullable=True),
        sa.Column('last_budget_month', sa.String(length=7), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_streak_user', 'user_streak', ['user_id'], unique=False)

    op.create_table('user_badge',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('badge_key', sa.String(length=50), nullable=False),
        sa.Column('badge_name', sa.String(length=100), nullable=False),
        sa.Column('badge_icon', sa.String(length=50), server_default='emoji_events'),
        sa.Column('badge_color', sa.String(length=20), server_default='#FFD700'),
        sa.Column('category', sa.String(length=30), server_default='general'),
        sa.Column('earned_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_badge_user', 'user_badge', ['user_id'], unique=False)


def downgrade():
    op.drop_index('ix_badge_user', table_name='user_badge')
    op.drop_table('user_badge')
    op.drop_index('ix_streak_user', table_name='user_streak')
    op.drop_table('user_streak')
