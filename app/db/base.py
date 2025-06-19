# app/db/base.py
# Import all models here to ensure they're registered with SQLAlchemy
# This file is used by Alembic for migrations

from app.db.base_class import Base  #Import the Base class
from app.models.tax_models import (
    DeductibleExpenseType,
    IncomeSource,
    MedicalTaxCredit,
    TaxBracket,
    TaxCalculation,
    TaxRebate,
    TaxThreshold,
    UserExpense,
    UserProfile,
)
