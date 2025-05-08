# app/db/base.py
from app.core.config import Base
from app.models.tax_models import (
    UserProfile, IncomeSource, UserExpense, DeductibleExpenseType,
    TaxBracket, TaxRebate, TaxThreshold, MedicalTaxCredit, TaxCalculation
)

# This file imports all models to ensure they're registered with the metadata
# Used by Alembic for migrations