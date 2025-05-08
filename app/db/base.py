# app/db/base.py
# Import all models here to ensure they're registered with SQLAlchemy
# This file is used by Alembic for migrations

from app.db.base_class import Base  # Import the Base class
from app.models.tax_models import (
    UserProfile, IncomeSource, UserExpense, DeductibleExpenseType,
    TaxBracket, TaxRebate, TaxThreshold, MedicalTaxCredit, TaxCalculation
)