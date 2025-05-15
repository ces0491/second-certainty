"""remove redundant indexes

Revision ID: 87c3e5f21a92
Revises: 6bd21db2c3ed
Create Date: 2025-05-15 14:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '87c3e5f21a92'
down_revision = '6bd21db2c3ed' # Update this to match your latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Remove redundant indexes
    op.drop_index('ix_deductible_expense_types_id', table_name='deductible_expense_types')
    op.drop_index('ix_income_sources_id', table_name='income_sources')
    op.drop_index('ix_medical_tax_credits_id', table_name='medical_tax_credits')
    op.drop_index('ix_tax_brackets_id', table_name='tax_brackets')
    op.drop_index('ix_tax_calculations_id', table_name='tax_calculations')
    op.drop_index('ix_tax_rebates_id', table_name='tax_rebates')
    op.drop_index('ix_tax_thresholds_id', table_name='tax_thresholds')
    op.drop_index('ix_user_expenses_id', table_name='user_expenses')
    op.drop_index('ix_user_profiles_id', table_name='user_profiles')


def downgrade():
    # Re-create indexes if needed to rollback
    op.create_index('ix_user_profiles_id', 'user_profiles', ['id'], unique=False)
    op.create_index('ix_user_expenses_id', 'user_expenses', ['id'], unique=False)
    op.create_index('ix_tax_thresholds_id', 'tax_thresholds', ['id'], unique=False)
    op.create_index('ix_tax_rebates_id', 'tax_rebates', ['id'], unique=False)
    op.create_index('ix_tax_calculations_id', 'tax_calculations', ['id'], unique=False)
    op.create_index('ix_tax_brackets_id', 'tax_brackets', ['id'], unique=False)
    op.create_index('ix_medical_tax_credits_id', 'medical_tax_credits', ['id'], unique=False)
    op.create_index('ix_income_sources_id', 'income_sources', ['id'], unique=False)
    op.create_index('ix_deductible_expense_types_id', 'deductible_expense_types', ['id'], unique=False)