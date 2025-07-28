# app/models/tax_models.py
from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class TaxBracket(Base):
    """Tax bracket for personal income tax."""

    __tablename__ = "tax_brackets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tax_year: Mapped[str] = mapped_column(String, index=True)  # e.g., "2024-2025"
    lower_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    upper_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Null for highest bracket
    rate: Mapped[float] = mapped_column(Float, nullable=False)  # Decimal rate (e.g., 0.18 for 18%)
    base_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # Base amount for this bracket


class TaxRebate(Base):
    """Tax rebates for different age groups."""

    __tablename__ = "tax_rebates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tax_year: Mapped[str] = mapped_column(String, index=True)
    primary: Mapped[float] = mapped_column(Float, nullable=False)  # Primary rebate for all taxpayers
    secondary: Mapped[float] = mapped_column(Float, nullable=False)  # Additional rebate for 65+
    tertiary: Mapped[float] = mapped_column(Float, nullable=False)  # Additional rebate for 75+


class TaxThreshold(Base):
    """Tax thresholds by age group."""

    __tablename__ = "tax_thresholds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tax_year: Mapped[str] = mapped_column(String, index=True)
    below_65: Mapped[int] = mapped_column(Integer, nullable=False)
    age_65_to_74: Mapped[int] = mapped_column(Integer, nullable=False)
    age_75_plus: Mapped[int] = mapped_column(Integer, nullable=False)


class MedicalTaxCredit(Base):
    """Medical scheme fees tax credits."""

    __tablename__ = "medical_tax_credits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tax_year: Mapped[str] = mapped_column(String, index=True)
    main_member: Mapped[float] = mapped_column(Float, nullable=False)
    additional_member: Mapped[float] = mapped_column(Float, nullable=False)


class DeductibleExpenseType(Base):
    """Types of expenses that can be deducted from taxable income."""

    __tablename__ = "deductible_expense_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    max_deduction: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Maximum deductible amount, if applicable
    max_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)  # Maximum percentage, if applicable
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserProfile(Base):
    """User profile information."""

    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    surname: Mapped[str] = mapped_column(String)
    date_of_birth: Mapped[date] = mapped_column(Date)
    hashed_password: Mapped[str] = mapped_column(String)
    is_provisional_taxpayer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    updated_at: Mapped[date | None] = mapped_column(Date, onupdate=func.current_date())

    # Relationships
    income_sources: Mapped[list["IncomeSource"]] = relationship("IncomeSource", back_populates="user")
    expenses: Mapped[list["UserExpense"]] = relationship("UserExpense", back_populates="user")
    tax_calculations: Mapped[list["TaxCalculation"]] = relationship("TaxCalculation", back_populates="user")


class IncomeSource(Base):
    """User income sources."""

    __tablename__ = "income_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profiles.id"))
    source_type: Mapped[str] = mapped_column(String)  # e.g., "Salary", "Rental", "Investment"
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    annual_amount: Mapped[float] = mapped_column(Float)
    is_paye: Mapped[bool] = mapped_column(Boolean, default=True)  # Whether PAYE is deducted from this income
    tax_year: Mapped[str] = mapped_column(String)
    created_at: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    updated_at: Mapped[date | None] = mapped_column(Date, onupdate=func.current_date())

    # Relationships
    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="income_sources")


class UserExpense(Base):
    """User deductible expenses."""

    __tablename__ = "user_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profiles.id"))
    expense_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("deductible_expense_types.id"))
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    amount: Mapped[float] = mapped_column(Float)
    tax_year: Mapped[str] = mapped_column(String)
    created_at: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    updated_at: Mapped[date | None] = mapped_column(Date, onupdate=func.current_date())

    # Relationships
    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="expenses")
    expense_type: Mapped["DeductibleExpenseType"] = relationship("DeductibleExpenseType")


class TaxCalculation(Base):
    """Stored tax calculations."""

    __tablename__ = "tax_calculations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profiles.id"))
    tax_year: Mapped[str] = mapped_column(String)
    gross_income: Mapped[float] = mapped_column(Float)
    taxable_income: Mapped[float] = mapped_column(Float)
    tax_liability: Mapped[float] = mapped_column(Float)
    tax_credits: Mapped[float] = mapped_column(Float)
    final_tax: Mapped[float] = mapped_column(Float)
    effective_tax_rate: Mapped[float] = mapped_column(Float)
    monthly_tax_rate: Mapped[float] = mapped_column(Float)
    calculation_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())

    # Relationships
    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="tax_calculations")
