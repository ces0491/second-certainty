# app/models/tax_models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List

from app.db.base_class import Base  # Import from the new location

class TaxBracket(Base):
    """Tax bracket for personal income tax."""
    __tablename__ = "tax_brackets"
    
    id = Column(Integer, primary_key=True, index=True)
    tax_year = Column(String, index=True)  # e.g., "2024-2025"
    lower_limit = Column(Integer, nullable=False)
    upper_limit = Column(Integer, nullable=True)  # Null for highest bracket
    rate = Column(Float, nullable=False)  # Decimal rate (e.g., 0.18 for 18%)
    base_amount = Column(Integer, nullable=False)  # Base amount for this bracket

class TaxRebate(Base):
    """Tax rebates for different age groups."""
    __tablename__ = "tax_rebates"
    
    id = Column(Integer, primary_key=True, index=True)
    tax_year = Column(String, index=True)
    primary = Column(Float, nullable=False)  # Primary rebate for all taxpayers
    secondary = Column(Float, nullable=False)  # Additional rebate for 65+
    tertiary = Column(Float, nullable=False)  # Additional rebate for 75+

class TaxThreshold(Base):
    """Tax thresholds by age group."""
    __tablename__ = "tax_thresholds"
    
    id = Column(Integer, primary_key=True, index=True)
    tax_year = Column(String, index=True)
    below_65 = Column(Integer, nullable=False)
    age_65_to_74 = Column(Integer, nullable=False)
    age_75_plus = Column(Integer, nullable=False)

class MedicalTaxCredit(Base):
    """Medical scheme fees tax credits."""
    __tablename__ = "medical_tax_credits"
    
    id = Column(Integer, primary_key=True, index=True)
    tax_year = Column(String, index=True)
    main_member = Column(Float, nullable=False)
    additional_member = Column(Float, nullable=False)

class DeductibleExpenseType(Base):
    """Types of expenses that can be deducted from taxable income."""
    __tablename__ = "deductible_expense_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    max_deduction = Column(Float, nullable=True)  # Maximum deductible amount, if applicable
    max_percentage = Column(Float, nullable=True)  # Maximum percentage, if applicable
    is_active = Column(Boolean, default=True)

class UserProfile(Base):
    """User profile information."""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    surname = Column(String)
    date_of_birth = Column(Date)
    hashed_password = Column(String) 
    is_provisional_taxpayer = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(Date, default=datetime.utcnow)
    updated_at = Column(Date, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    income_sources = relationship("IncomeSource", back_populates="user")
    expenses = relationship("UserExpense", back_populates="user")
    tax_calculations = relationship("TaxCalculation", back_populates="user")

class IncomeSource(Base):
    """User income sources."""
    __tablename__ = "income_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"))
    source_type = Column(String)  # e.g., "Salary", "Rental", "Investment"
    description = Column(String, nullable=True)
    annual_amount = Column(Float)
    is_paye = Column(Boolean, default=True)  # Whether PAYE is deducted from this income
    tax_year = Column(String)
    created_at = Column(Date, default=datetime.utcnow)
    updated_at = Column(Date, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserProfile", back_populates="income_sources")

class UserExpense(Base):
    """User deductible expenses."""
    __tablename__ = "user_expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"))
    expense_type_id = Column(Integer, ForeignKey("deductible_expense_types.id"))
    description = Column(String, nullable=True)
    amount = Column(Float)
    tax_year = Column(String)
    created_at = Column(Date, default=datetime.utcnow)
    updated_at = Column(Date, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserProfile", back_populates="expenses")
    expense_type = relationship("DeductibleExpenseType")

class TaxCalculation(Base):
    """Stored tax calculations."""
    __tablename__ = "tax_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"))
    tax_year = Column(String)
    gross_income = Column(Float)
    taxable_income = Column(Float)
    tax_liability = Column(Float)
    tax_credits = Column(Float)
    final_tax = Column(Float)
    effective_tax_rate = Column(Float)  # As a decimal
    monthly_tax_rate = Column(Float)  # As a decimal
    calculation_date = Column(Date, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserProfile", back_populates="tax_calculations")