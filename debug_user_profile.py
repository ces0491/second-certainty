# debug_user_profile.py
import sys
import os
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.config import get_db
from app.models.tax_models import UserProfile, IncomeSource, UserExpense

def debug_user_profile(user_id: int):
    """Debug user profile and related data."""
    db = next(get_db())
    try:
        # Get user profile
        user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not user:
            print(f"❌ User with ID {user_id} not found")
            return
        
        print(f"👤 User Profile for ID {user_id}:")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.name} {user.surname}")
        print(f"   Is Provisional Taxpayer: {user.is_provisional_taxpayer}")
        print(f"   Date of Birth: {user.date_of_birth}")
        
        # Check income sources for current tax year
        current_tax_year = "2025-2026"
        income_sources = db.query(IncomeSource).filter(
            IncomeSource.user_id == user_id,
            IncomeSource.tax_year == current_tax_year
        ).all()
        
        print(f"\n💰 Income Sources for {current_tax_year}:")
        if income_sources:
            total_income = 0
            for income in income_sources:
                print(f"   - {income.source_type}: R{income.annual_amount:,.2f}")
                total_income += income.annual_amount
            print(f"   Total Income: R{total_income:,.2f}")
        else:
            print("   ❌ No income sources found")
        
        # Check expenses
        expenses = db.query(UserExpense).filter(
            UserExpense.user_id == user_id,
            UserExpense.tax_year == current_tax_year
        ).all()
        
        print(f"\n📊 Expenses for {current_tax_year}:")
        if expenses:
            total_expenses = 0
            for expense in expenses:
                print(f"   - {expense.description}: R{expense.amount:,.2f}")
                total_expenses += expense.amount
            print(f"   Total Expenses: R{total_expenses:,.2f}")
        else:
            print("   No expenses found")
            
    except Exception as e:
        print(f"❌ Error debugging user profile: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_user_profile.py <user_id>")
        sys.exit(1)
    
    user_id = int(sys.argv[1])
    debug_user_profile(user_id)