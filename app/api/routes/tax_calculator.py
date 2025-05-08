# app/api/routes/tax_calculator.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date

from app.core.config import get_db
from app.core.tax_calculator import TaxCalculator
from app.core.data_scraper import SARSDataScraper
from app.models.tax_models import UserProfile, IncomeSource, UserExpense, DeductibleExpenseType
from app.utils.tax_utils import get_tax_year

from pydantic import BaseModel, Field

router = APIRouter()

# Pydantic models for request/response
class IncomeSourceCreate(BaseModel):
    source_type: str
    description: Optional[str] = None
    annual_amount: float
    is_paye: bool = True
    tax_year: Optional[str] = None

class ExpenseCreate(BaseModel):
    expense_type_id: int
    description: Optional[str] = None
    amount: float
    tax_year: Optional[str] = None

class UserProfileCreate(BaseModel):
    email: str
    name: str
    surname: str
    date_of_birth: date
    is_provisional_taxpayer: bool = False

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


@router.post("/users/", status_code=status.HTTP_201_CREATED)
def create_user(user: UserProfileCreate, db: Session = Depends(get_db)):
    """Create a new user profile."""
    db_user = UserProfile(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/users/{user_id}/income/", status_code=status.HTTP_201_CREATED)
def add_income_source(user_id: int, income: IncomeSourceCreate, db: Session = Depends(get_db)):
    """Add an income source for a user."""
    # Check if user exists
    db_user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Set default tax year if not provided
    if not income.tax_year:
        income.tax_year = get_tax_year()
    
    # Create income source
    db_income = IncomeSource(**income.dict(), user_id=user_id)
    db.add(db_income)
    db.commit()
    db.refresh(db_income)
    return db_income

@router.post("/users/{user_id}/expenses/", status_code=status.HTTP_201_CREATED)
def add_expense(user_id: int, expense: ExpenseCreate, db: Session = Depends(get_db)):
    """Add a deductible expense for a user."""
    # Check if user exists
    db_user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if expense type exists
    db_expense_type = db.query(DeductibleExpenseType).filter(
        DeductibleExpenseType.id == expense.expense_type_id
    ).first()
    if not db_expense_type:
        raise HTTPException(status_code=404, detail="Expense type not found")
    
    # Set default tax year if not provided
    if not expense.tax_year:
        expense.tax_year = get_tax_year()
    
    # Create expense
    db_expense = UserExpense(**expense.dict(), user_id=user_id)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@router.get("/tax-brackets/", response_model=List[TaxBracketResponse])
def get_tax_brackets(tax_year: Optional[str] = None, db: Session = Depends(get_db)):
    """Get tax brackets for a specific tax year."""
    if not tax_year:
        tax_year = get_tax_year()
    
    calculator = TaxCalculator(db)
    brackets = calculator.get_tax_brackets(tax_year)
    
    # Convert to response model
    response_brackets = [
        TaxBracketResponse(
            lower_limit=bracket["lower_limit"],
            upper_limit=bracket["upper_limit"],
            rate=bracket["rate"],
            base_amount=bracket["base_amount"],
            tax_year=tax_year
        )
        for bracket in brackets
    ]
    
    return response_brackets

@router.get("/deductible-expenses/", response_model=List[DeductibleExpenseTypeResponse])
def get_deductible_expense_types(db: Session = Depends(get_db)):
    """Get all types of deductible expenses."""
    expense_types = db.query(DeductibleExpenseType).filter(
        DeductibleExpenseType.is_active == True
    ).all()
    
    return expense_types

@router.get("/users/{user_id}/tax-calculation/", response_model=TaxCalculationResponse)
def calculate_tax(user_id: int, tax_year: Optional[str] = None, db: Session = Depends(get_db)):
    """Calculate tax liability for a user."""
    if not tax_year:
        tax_year = get_tax_year()
    
    calculator = TaxCalculator(db)
    try:
        result = calculator.calculate_tax_liability(user_id, tax_year)
        return TaxCalculationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/users/{user_id}/provisional-tax/", response_model=ProvisionalTaxResponse)
def calculate_provisional_tax(user_id: int, tax_year: Optional[str] = None, db: Session = Depends(get_db)):
    """Calculate provisional tax for a provisional taxpayer."""
    if not tax_year:
        tax_year = get_tax_year()
    
    calculator = TaxCalculator(db)
    try:
        result = calculator.calculate_provisional_tax(user_id, tax_year)
        return ProvisionalTaxResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update-tax-data/")
async def update_tax_data(db: Session = Depends(get_db)):
    """
    Update tax data by scraping the SARS website.
    This should be run periodically to ensure tax data is current.
    """
    scraper = SARSDataScraper()
    try:
        result = await scraper.update_tax_data(db)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update tax data: {str(e)}")