# scripts/seed_data.py
import asyncio
import sys
import os

# Add parent directory to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.models.tax_models import DeductibleExpenseType, TaxBracket, TaxRebate, TaxThreshold, MedicalTaxCredit
from app.core.config import get_db, engine
from app.models.tax_models import Base
from app.core.data_scraper import SARSDataScraper

# Create the database tables
Base.metadata.create_all(bind=engine)

async def seed_deductible_expense_types(db: Session):
    """Seed the deductible expense types."""
    expense_types = [
        {
            "name": "Retirement Annuity Contributions",
            "description": "Contributions to retirement annuities",
            "max_percentage": 27.5,  # 27.5% of remuneration or taxable income
            "max_deduction": 350000,  # Annual maximum
            "is_active": True
        },
        {
            "name": "Medical Expenses",
            "description": "Out-of-pocket medical expenses not covered by medical aid",
            "max_percentage": None,
            "max_deduction": None,  # Complex rules based on age and circumstances
            "is_active": True
        },
        {
            "name": "Home Office Expenses",
            "description": "Expenses for maintaining a home office if you work from home",
            "max_percentage": None,
            "max_deduction": None,
            "is_active": True
        },
        {
            "name": "Donations to Public Benefit Organizations",
            "description": "Donations to approved public benefit organizations",
            "max_percentage": 10,  # 10% of taxable income
            "max_deduction": None,
            "is_active": True
        },
        {
            "name": "Travel Expenses",
            "description": "Business-related travel expenses",
            "max_percentage": None,
            "max_deduction": None,
            "is_active": True
        }
    ]
    
    # Check if data already exists
    existing = db.query(DeductibleExpenseType).first()
    if existing:
        print("Deductible expense types already exist, skipping seeding.")
        return
    
    for expense_type in expense_types:
        db_expense_type = DeductibleExpenseType(**expense_type)
        db.add(db_expense_type)
    
    db.commit()
    print("Deductible expense types seeded successfully.")

async def seed_tax_data(db: Session):
    """Seed tax brackets, rebates, thresholds, and medical credits."""
    # Initialize the scraper
    scraper = SARSDataScraper()
    
    # Check if tax data already exists for the current tax year
    tax_year = scraper.get_tax_year()
    existing = db.query(TaxBracket).filter(TaxBracket.tax_year == tax_year).first()
    
    if existing:
        print(f"Tax data for {tax_year} already exists, skipping seeding.")
        return
    
    try:
        # Use the scraper to update tax data
        result = await scraper.update_tax_data(db)
        print(f"Tax data for {tax_year} seeded successfully.")
        return result
    except Exception as e:
        print(f"Error seeding tax data: {e}")
        raise

async def main():
    db = next(get_db())
    try:
        await seed_deductible_expense_types(db)
        await seed_tax_data(db)
        print("All seed data created successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())