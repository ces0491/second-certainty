# app/api/routes/tax_calculator.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.config import get_db
from app.core.tax_calculator import TaxCalculator
from app.core.data_scraper import SARSDataScraper
from app.models.tax_models import UserProfile, IncomeSource, UserExpense, DeductibleExpenseType
from app.utils.tax_utils import get_tax_year
from app.core.auth import get_current_user
from app.schemas.tax_schemas import (
    IncomeCreate, IncomeResponse, ExpenseCreate, ExpenseResponse, 
    TaxBracketResponse, TaxCalculationResponse, ProvisionalTaxResponse, 
    DeductibleExpenseTypeResponse
)

router = APIRouter()

@router.post("/users/{user_id}/income/", response_model=IncomeResponse, status_code=status.HTTP_201_CREATED)
def add_income_source(
    user_id: int, 
    income: IncomeCreate, 
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Add an income source for a user."""
    # Security: Ensure users can only add income to their own profile
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to add income to this user"
        )
    
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

@router.get("/users/{user_id}/income/", response_model=List[IncomeResponse])
def get_user_income(
    user_id: int,
    tax_year: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Get all income sources for a user."""
    # Security: Ensure users can only view their own income
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to view this user's income"
        )
    
    # Set default tax year if not provided
    if not tax_year:
        tax_year = get_tax_year()
    
    income_sources = db.query(IncomeSource).filter(
        IncomeSource.user_id == user_id,
        IncomeSource.tax_year == tax_year
    ).all()
    
    return income_sources

@router.post("/users/{user_id}/expenses/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def add_expense(
    user_id: int, 
    expense: ExpenseCreate, 
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Add a deductible expense for a user."""
    # Security: Ensure users can only add expenses to their own profile
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to add expenses to this user"
        )
    
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

@router.get("/users/{user_id}/expenses/", response_model=List[ExpenseResponse])
def get_user_expenses(
    user_id: int,
    tax_year: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Get all expenses for a user."""
    # Security: Ensure users can only view their own expenses
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to view this user's expenses"
        )
    
    # Set default tax year if not provided
    if not tax_year:
        tax_year = get_tax_year()
    
    expenses = db.query(UserExpense).filter(
        UserExpense.user_id == user_id,
        UserExpense.tax_year == tax_year
    ).all()
    
    return expenses

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
def calculate_tax(
    user_id: int, 
    tax_year: Optional[str] = None, 
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Calculate tax liability for a user."""
    # Security: Ensure users can only calculate their own tax
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to calculate tax for this user"
        )
    
    if not tax_year:
        tax_year = get_tax_year()
    
    calculator = TaxCalculator(db)
    try:
        result = calculator.calculate_tax_liability(user_id, tax_year)
        return TaxCalculationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/users/{user_id}/provisional-tax/", response_model=ProvisionalTaxResponse)
def calculate_provisional_tax(
    user_id: int, 
    tax_year: Optional[str] = None, 
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Calculate provisional tax for a provisional taxpayer."""
    # Security: Ensure users can only calculate their own provisional tax
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to calculate provisional tax for this user"
        )
    
    if not tax_year:
        tax_year = get_tax_year()
    
    calculator = TaxCalculator(db)
    try:
        result = calculator.calculate_provisional_tax(user_id, tax_year)
        return ProvisionalTaxResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update-tax-data/")
async def update_tax_data(
    db: Session = Depends(get_db), 
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Update tax data by scraping the SARS website.
    This should be run periodically to ensure tax data is current.
    """
    # This is an admin operation, so we should have a check that the user is an admin
    # For now, we'll just allow any authenticated user to update tax data
    scraper = SARSDataScraper()
    try:
        result = await scraper.update_tax_data(db)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update tax data: {str(e)}")

@router.delete("/users/{user_id}/income/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income(
    user_id: int,
    income_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Delete an income source."""
    # Security: Ensure users can only delete their own income
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to delete this income"
        )
    
    income = db.query(IncomeSource).filter(
        IncomeSource.id == income_id,
        IncomeSource.user_id == user_id
    ).first()
    
    if not income:
        raise HTTPException(status_code=404, detail="Income source not found")
    
    db.delete(income)
    db.commit()
    return None

@router.delete("/users/{user_id}/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    user_id: int,
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Delete an expense."""
    # Security: Ensure users can only delete their own expenses
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to delete this expense"
        )
    
    expense = db.query(UserExpense).filter(
        UserExpense.id == expense_id,
        UserExpense.user_id == user_id
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.delete(expense)
    db.commit()
    return None