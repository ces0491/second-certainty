# app/schemas/tax_schemas.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import date
from decimal import Decimal

# User schemas
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
    
    @validator('name', 'surname')
    def validate_names(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Name fields cannot be empty')
        return v.strip() if v else v
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        if v is not None and v >= date.today():
            raise ValueError('Date of birth must be in the past')
        return v

class UserResponse(UserBase):
    id: int
    created_at: date
    is_admin: Optional[bool] = False

    class Config:
        from_attributes = True

# Income schemas
class IncomeBase(BaseModel):
    description: str
    amount: Decimal
    date_received: date
    income_type: str

class IncomeCreate(IncomeBase):
    pass

class IncomeUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    date_received: Optional[date] = None
    income_type: Optional[str] = None

class IncomeResponse(IncomeBase):
    id: int
    user_id: int
    created_at: date

    class Config:
        from_attributes = True

# Expense schemas
class ExpenseBase(BaseModel):
    description: str
    amount: Decimal
    date_incurred: date
    expense_type: str

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    date_incurred: Optional[date] = None
    expense_type: Optional[str] = None

class ExpenseResponse(ExpenseBase):
    id: int
    user_id: int
    created_at: date

    class Config:
        from_attributes = True

# Tax calculation schemas
class TaxCalculationRequest(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    is_provisional_taxpayer: bool = False

class TaxBracket(BaseModel):
    min_income: Decimal
    max_income: Optional[Decimal]
    rate: Decimal
    threshold: Decimal

class TaxCalculationResponse(BaseModel):
    taxable_income: Decimal
    total_tax: Decimal
    tax_brackets: List[TaxBracket]
    effective_rate: Decimal
    marginal_rate: Decimal
    provisional_payments: Optional[Decimal] = None

    class Config:
        from_attributes = True

# Provisional tax schemas
class ProvisionalTaxBase(BaseModel):
    period: str
    estimated_income: Decimal
    estimated_expenses: Decimal
    payment_amount: Decimal
    due_date: date

class ProvisionalTaxCreate(ProvisionalTaxBase):
    pass

class ProvisionalTaxUpdate(BaseModel):
    estimated_income: Optional[Decimal] = None
    estimated_expenses: Optional[Decimal] = None
    payment_amount: Optional[Decimal] = None
    due_date: Optional[date] = None

class ProvisionalTaxResponse(ProvisionalTaxBase):
    id: int
    user_id: int
    payment_status: str
    created_at: date

    class Config:
        from_attributes = True