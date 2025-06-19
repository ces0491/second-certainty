# app/schemas/tax_schemas.py
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, validator


class DeductibleExpenseTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    max_deduction: Optional[float] = None
    max_percentage: Optional[float] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class ExpenseResponse(BaseModel):
    id: int
    user_id: int
    expense_type_id: int
    description: Optional[str] = None
    amount: float
    tax_year: Optional[str] = None
    created_at: date
    expense_type: Optional[DeductibleExpenseTypeResponse] = None

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr
    name: str
    surname: str
    date_of_birth: date
    is_provisional_taxpayer: bool = False


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    """User profile update model - all fields are optional"""

    name: Optional[str] = None
    surname: Optional[str] = None
    date_of_birth: Optional[date] = None
    is_provisional_taxpayer: Optional[bool] = None

    @validator("name", "surname")
    def validate_names(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Name fields cannot be empty")
        return v.strip() if v else v

    @validator("date_of_birth")
    def validate_date_of_birth(cls, v):
        if v is not None and v >= date.today():
            raise ValueError("Date of birth must be in the past")
        return v


class UserResponse(UserBase):
    id: int
    created_at: date
    is_admin: Optional[bool] = False

    class Config:
        from_attributes = True


# Income schemas
class IncomeBase(BaseModel):
    source_type: str
    description: Optional[str] = None
    annual_amount: float
    is_paye: bool = True
    tax_year: Optional[str] = None


class IncomeCreate(IncomeBase):
    pass


class IncomeUpdate(BaseModel):
    source_type: Optional[str] = None
    description: Optional[str] = None
    annual_amount: Optional[float] = None
    is_paye: Optional[bool] = None
    tax_year: Optional[str] = None


class IncomeResponse(IncomeBase):
    id: int
    user_id: int
    created_at: date

    class Config:
        from_attributes = True


# Expense schemas
class ExpenseBase(BaseModel):
    expense_type_id: int
    description: Optional[str] = None
    amount: float
    tax_year: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    expense_type_id: Optional[int] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    tax_year: Optional[str] = None


# Tax bracket schemas
class TaxBracketBase(BaseModel):
    lower_limit: int
    upper_limit: Optional[int] = None
    rate: float
    base_amount: int
    tax_year: str


class TaxBracketResponse(TaxBracketBase):
    class Config:
        from_attributes = True


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
    class Config:
        from_attributes = True


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
    total_tax: float
    taxable_income: float
    effective_tax_rate: float
    first_payment: PaymentInfo
    second_payment: PaymentInfo

    class Config:
        from_attributes = True


# Legacy schemas for backward compatibility
class TaxCalculationRequest(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    is_provisional_taxpayer: bool = False


class TaxBracket(BaseModel):
    min_income: Decimal
    max_income: Optional[Decimal]
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
    estimated_income: Optional[Decimal] = None
    estimated_expenses: Optional[Decimal] = None
    payment_amount: Optional[Decimal] = None
    due_date: Optional[date] = None
