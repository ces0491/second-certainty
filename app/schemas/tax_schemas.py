# app/schemas/tax_schemas.py (update this empty file)
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    surname: str
    date_of_birth: date
    is_provisional_taxpayer: bool = False

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: date
    is_admin: Optional[bool] = False

    class Config:
        orm_mode = True

# Income schemas
class IncomeBase(BaseModel):
    source_type: str
    description: Optional[str] = None
    annual_amount: float
    is_paye: bool = True
    tax_year: Optional[str] = None

class IncomeCreate(IncomeBase):
    pass

class IncomeResponse(IncomeBase):
    id: int
    user_id: int
    created_at: date

    class Config:
        orm_mode = True

# Expense schemas
class ExpenseBase(BaseModel):
    expense_type_id: int
    description: Optional[str] = None
    amount: float
    tax_year: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseResponse(ExpenseBase):
    id: int
    user_id: int
    created_at: date

    class Config:
        orm_mode = True

# Tax calculation schemas
class TaxBracketResponse(BaseModel):
    lower_limit: int
    upper_limit: Optional[int] = None
    rate: float
    base_amount: int
    tax_year: str

class TaxCalculationResponse(BaseModel):
    gross_income: float
    taxable_income: float
    tax_before_rebates: float
    rebates: float
    medical_credits: float
    final_tax: float
    effective_tax_rate: float
    monthly_tax_rate: float

class ProvisionalTaxResponse(BaseModel):
    annual_tax: float
    first_payment: float
    second_payment: float
    final_payment: float

class DeductibleExpenseTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    max_deduction: Optional[float] = None
    max_percentage: Optional[float] = None

    class Config:
        orm_mode = True