#scripts/seed_data.py
import asyncio
import logging
import os
import sys

from sqlalchemy.orm import Session

from app.models.tax_models import (
    Base,
    DeductibleExpenseType,
    MedicalTaxCredit,
    TaxBracket,
    TaxRebate,
    TaxThreshold,
)

#Add parent directory to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import engine, get_db
from app.core.data_scraper import SARSDataScraper
from app.models.tax_models import (
    Base,
    DeductibleExpenseType,
    MedicalTaxCredit,
    TaxBracket,
    TaxRebate,
    TaxThreshold,
)
from app.utils.tax_utils import get_tax_year

#Create the database tables
Base.metadata.create_all(bind=engine)


async def seed_deductible_expense_types(db: Session):
    """Seed the deductible expense types."""
    expense_types = [
        {
            "name": "Retirement Annuity Contributions",
            "description": "Contributions to retirement annuities",
            "max_percentage": 27.5,  #27.5% of remuneration or taxable income
            "max_deduction": 350000,  #Annual maximum
            "is_active": True,
        },
        {
            "name": "Medical Expenses",
            "description": "Out-of-pocket medical expenses not covered by medical aid",
            "max_percentage": None,
            "max_deduction": None,  #Complex rules based on age and circumstances
            "is_active": True,
        },
        {
            "name": "Home Office Expenses",
            "description": "Expenses for maintaining a home office if you work from home",
            "max_percentage": None,
            "max_deduction": None,
            "is_active": True,
        },
        {
            "name": "Donations to Public Benefit Organizations",
            "description": "Donations to approved public benefit organizations",
            "max_percentage": 10,  #10% of taxable income
            "max_deduction": None,
            "is_active": True,
        },
        {
            "name": "Travel Expenses",
            "description": "Business-related travel expenses",
            "max_percentage": None,
            "max_deduction": None,
            "is_active": True,
        },
    ]

    #Check if data already exists
    existing = db.query(DeductibleExpenseType).first()
    if existing:
        print("Deductible expense types already exist, skipping seeding.")
        return

    for expense_type in expense_types:
        db_expense_type = DeductibleExpenseType(**expense_type)
        db.add(db_expense_type)

    db.commit()
    print("Deductible expense types seeded successfully.")


async def seed_tax_data_manually(db: Session, tax_year: str):
    """
    Manually seed tax data when scraping fails.
    Uses the latest known tax brackets for South Africa.
    """
    try:
        print(f"Manually seeding tax data for {tax_year}...")

        #Clear existing data for this tax year
        db.query(TaxBracket).filter(TaxBracket.tax_year == tax_year).delete()
        db.query(TaxRebate).filter(TaxRebate.tax_year == tax_year).delete()
        db.query(TaxThreshold).filter(TaxThreshold.tax_year == tax_year).delete()
        db.query(MedicalTaxCredit).filter(MedicalTaxCredit.tax_year == tax_year).delete()

        #Add tax brackets for 2024-2025 tax year
        #Based on latest available data
        brackets = [
            {"lower_limit": 1, "upper_limit": 237100, "rate": 0.18, "base_amount": 0, "tax_year": tax_year},
            {"lower_limit": 237101, "upper_limit": 370500, "rate": 0.26, "base_amount": 42678, "tax_year": tax_year},
            {"lower_limit": 370501, "upper_limit": 512800, "rate": 0.31, "base_amount": 77362, "tax_year": tax_year},
            {"lower_limit": 512801, "upper_limit": 673000, "rate": 0.36, "base_amount": 121475, "tax_year": tax_year},
            {"lower_limit": 673001, "upper_limit": 857900, "rate": 0.39, "base_amount": 179147, "tax_year": tax_year},
            {"lower_limit": 857901, "upper_limit": 1817000, "rate": 0.41, "base_amount": 251258, "tax_year": tax_year},
            {"lower_limit": 1817001, "upper_limit": None, "rate": 0.45, "base_amount": 644489, "tax_year": tax_year},
        ]

        #Add rebates
        rebate = {
            "primary": 17235,
            "secondary": 9444,  #For persons 65 and older
            "tertiary": 3145,  #For persons 75 and older
            "tax_year": tax_year,
        }

        #Add thresholds
        threshold = {"below_65": 95750, "age_65_to_74": 148217, "age_75_plus": 165689, "tax_year": tax_year}

        #Add medical credits
        medical_credit = {"main_member": 347, "additional_member": 347, "tax_year": tax_year}

        #Insert data into database
        for bracket in brackets:
            db.add(TaxBracket(**bracket))

        db.add(TaxRebate(**rebate))
        db.add(TaxThreshold(**threshold))
        db.add(MedicalTaxCredit(**medical_credit))

        #Commit changes
        db.commit()
        print(f"Tax data for {tax_year} manually seeded successfully!")

        return {
            "tax_year": tax_year,
            "brackets": brackets,
            "rebates": rebate,
            "thresholds": threshold,
            "medical_credits": medical_credit,
        }
    except Exception as e:
        print(f"Error manually seeding tax data: {e}")
        db.rollback()
        raise


async def seed_tax_data(db: Session):
    """Seed tax brackets, rebates, thresholds, and medical credits."""
    #Initialize the scraper
    scraper = SARSDataScraper()

    #Get the current tax year
    tax_year = get_tax_year()

    #Check if tax data already exists for the current tax year
    existing = db.query(TaxBracket).filter(TaxBracket.tax_year == tax_year).first()

    if existing:
        print(f"Tax data for {tax_year} already exists, skipping seeding.")
        return

    try:
        #Try to use the scraper to update tax data
        print(f"Attempting to scrape tax data for {tax_year} from SARS website...")
        result = await scraper.update_tax_data(db)
        print(f"Tax data for {tax_year} scraped and seeded successfully.")
        return result
    except Exception as e:
        print(f"Error scraping tax data: {e}")
        print("Falling back to manual tax data entry...")

        #Fall back to manual seeding if scraping fails
        result = await seed_tax_data_manually(db, tax_year)
        return result


async def initialize_database(db: Session, current_tax_year: str = None):
    """
    Initialize the database with required seed data.
    Can be used during startup or manually via script.

    Args:
        db: Database session
        current_tax_year: The current tax year (optional, defaults to calculated value)
    """
    try:
        logger = logging.getLogger("initialize_database")

        #If tax year not specified, calculate it
        if not current_tax_year:
            current_tax_year = get_tax_year()

        logger.info(f"Initializing database for tax year {current_tax_year}")

        #Seed deductible expense types
        await seed_deductible_expense_types(db)

        #Initialize tax data
        try:
            #First try to get current tax year data
            scraper = SARSDataScraper()
            await scraper.update_tax_data(db, current_tax_year)
            logger.info(f"Successfully initialized tax data for {current_tax_year}")
        except Exception as e:
            logger.warning(f"Could not retrieve current tax year data: {e}")
            logger.info("Falling back to previous tax year data...")

            #If current year fails, try previous tax year
            previous_year_start = int(current_tax_year.split("-")[0]) - 1
            previous_year_end = int(current_tax_year.split("-")[1]) - 1
            previous_tax_year = f"{previous_year_start}-{previous_year_end}"

            #Check if we already have data for the previous year
            existing = db.query(TaxBracket).filter(TaxBracket.tax_year == previous_tax_year).first()

            if existing:
                logger.info(f"Using existing {previous_tax_year} tax data")
                #Copy previous year data to current year
                await copy_tax_year_data(db, previous_tax_year, current_tax_year)
            else:
                #Try to scrape previous year data
                try:
                    await scraper.update_tax_data(db, previous_tax_year)
                    await copy_tax_year_data(db, previous_tax_year, current_tax_year)
                except Exception as e2:
                    logger.error(f"Could not retrieve previous tax year data: {e2}")
                    logger.info("Falling back to manual tax data entry...")
                    #Use the manual seed function
                    await seed_tax_data_manually(db, current_tax_year)

        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        raise


async def copy_tax_year_data(db: Session, source_year: str, target_year: str):
    """Copy tax data from one year to another when SARS hasn't updated yet."""
    logger = logging.getLogger("copy_tax_year_data")
    logger.info(f"Copying tax data from {source_year} to {target_year}...")

    #Get source year tax brackets
    brackets = db.query(TaxBracket).filter(TaxBracket.tax_year == source_year).all()
    rebate = db.query(TaxRebate).filter(TaxRebate.tax_year == source_year).first()
    threshold = db.query(TaxThreshold).filter(TaxThreshold.tax_year == source_year).first()
    medical = db.query(MedicalTaxCredit).filter(MedicalTaxCredit.tax_year == source_year).first()

    #Clear any existing data for target year
    db.query(TaxBracket).filter(TaxBracket.tax_year == target_year).delete()
    db.query(TaxRebate).filter(TaxRebate.tax_year == target_year).delete()
    db.query(TaxThreshold).filter(TaxThreshold.tax_year == target_year).delete()
    db.query(MedicalTaxCredit).filter(MedicalTaxCredit.tax_year == target_year).delete()

    #Copy brackets with new tax year
    for bracket in brackets:
        new_bracket = TaxBracket(
            lower_limit=bracket.lower_limit,
            upper_limit=bracket.upper_limit,
            rate=bracket.rate,
            base_amount=bracket.base_amount,
            tax_year=target_year,
        )
        db.add(new_bracket)

    #Copy rebate
    if rebate:
        new_rebate = TaxRebate(
            primary=rebate.primary, secondary=rebate.secondary, tertiary=rebate.tertiary, tax_year=target_year
        )
        db.add(new_rebate)

    #Copy threshold
    if threshold:
        new_threshold = TaxThreshold(
            below_65=threshold.below_65,
            age_65_to_74=threshold.age_65_to_74,
            age_75_plus=threshold.age_75_plus,
            tax_year=target_year,
        )
        db.add(new_threshold)

    #Copy medical credits
    if medical:
        new_medical = MedicalTaxCredit(
            main_member=medical.main_member, additional_member=medical.additional_member, tax_year=target_year
        )
        db.add(new_medical)

    #Commit all changes
    db.commit()
    logger.info(f"Successfully copied tax data from {source_year} to {target_year}")


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
