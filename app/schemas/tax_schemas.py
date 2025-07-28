# app/schemas/tax_schemas.py
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict


class DeductibleExpenseTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    max_deduction: float | None = None
    max_percentage: float | None = None
    is_active: bool = True


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    expense_type_id: int
    description: str | None = None
    amount: float
    tax_year: str | None = None
    created_at: date
    expense_type: DeductibleExpenseTypeResponse | None = None


class UserBase(BaseModel):
    email: EmailStr
    name: str
    surname: str
    date_of_birth: date
    is_provisional_taxpayer: bool = False


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if v.isdigit():
            raise ValueError("Password cannot be only numbers")
        if v.isalpha():
            raise ValueError("Password cannot be only letters")
        if v.lower() in ["password", "12345678", "abcdefgh", "123"]:
            raise ValueError("Password is too common")
        return v


class UserUpdate(BaseModel):
    """User profile update model - all fields are optional"""
    name: str | None = None
    surname: str | None = None
    date_of_birth: date | None = None
    is_provisional_taxpayer: bool | None = None

    @field_validator("name", "surname")
    @classmethod
    def validate_names(cls, v: str | None) -> str | None:
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Name fields cannot be empty")
        return v.strip() if v else v

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: date | None) -> date | None:
        if v is not None and v >= date.today():
            raise ValueError("Date of birth must be in the past")
        return v


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: date | None = None  # Allow None temporarily
    is_admin: bool | None = False
    
    @field_validator('created_at', mode='before')
    @classmethod
    def validate_created_at(cls, v):
        """Ensure created_at is never None - use current date as fallback."""
        if v is None:
            from datetime import datetime, timezone
            return datetime.now(timezone.utc).date()
        return v


# Income schemas
class IncomeBase(BaseModel):
    source_type: str
    description: str | None = None
    annual_amount: float
    is_paye: bool = True
    tax_year: str | None = None


class IncomeCreate(IncomeBase):
    @field_validator("annual_amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Annual amount must be positive")
        return v


class IncomeUpdate(BaseModel):
    source_type: str | None = None
    description: str | None = None
    annual_amount: float | None = None
    is_paye: bool | None = None
    tax_year: str | None = None


class IncomeResponse(IncomeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: date


# Expense schemas
class ExpenseBase(BaseModel):
    expense_type_id: int
    description: str | None = None
    amount: float
    tax_year: str | None = None


class ExpenseCreate(ExpenseBase):
    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Expense amount must be positive")
        return v


class ExpenseUpdate(BaseModel):
    expense_type_id: int | None = None
    description: str | None = None
    amount: float | None = None
    tax_year: str | None = None


# Tax bracket schemas
class TaxBracketBase(BaseModel):
    lower_limit: int
    upper_limit: int | None = None
    rate: float
    base_amount: int
    tax_year: str


class TaxBracketResponse(TaxBracketBase):
    model_config = ConfigDict(from_attributes=True)


# Tax calculation schemas
class TaxCalculationBase(BaseModel):
    gross_income: float
    taxable_income: float
    tax_before_rebates: float
    rebates: float
    medical_credits: float
    final_tax: float
    effective_tax_rate: float
    monthly_tax_rate: float


class TaxCalculationResponse(TaxCalculationBase):
    model_config = ConfigDict(from_attributes=True)


# Provisional tax schemas
class ProvisionalTaxBase(BaseModel):
    annual_tax: float
    first_payment: float
    second_payment: float
    final_payment: float


class PaymentInfo(BaseModel):
    amount: float
    due_date: str


class ProvisionalTaxResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_tax: float
    taxable_income: float
    effective_tax_rate: float
    first_payment: PaymentInfo
    second_payment: PaymentInfo


# Legacy schemas for backward compatibility
class TaxCalculationRequest(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    is_provisional_taxpayer: bool = False


class TaxBracket(BaseModel):
    min_income: Decimal
    max_income: Decimal | None = None
    rate: Decimal
    threshold: Decimal


# Provisional tax legacy schemas
class ProvisionalTaxCreate(BaseModel):
    period: str
    estimated_income: Decimal
    estimated_expenses: Decimal
    payment_amount: Decimal
    due_date: date


class ProvisionalTaxUpdate(BaseModel):
    estimated_income: Decimal | None = None
    estimated_expenses: Decimal | None = None
    payment_amount: Decimal | None = None
    due_date: date | None = None
