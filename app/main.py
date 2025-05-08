# app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy.orm import Session

from app.core.config import settings, get_db, engine
from app.models.tax_models import Base
from app.api.routes import tax_calculator
from app.core.data_scraper import SARSDataScraper
from app.models.tax_models import TaxBracket, TaxRebate, TaxThreshold, MedicalTaxCredit
from app.utils.tax_utils import get_tax_year
from app.api.routes import admin

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="South African tax liability management API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, limit this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    tax_calculator.router,
    prefix=f"{settings.API_PREFIX}/tax",
    tags=["tax"]
)

# Include the admin router
app.include_router(
    admin.router,
    prefix=f"{settings.API_PREFIX}/admin",
    tags=["admin"]
)

@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "Welcome to the Second Certainty Tax API"
    }

@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    import subprocess
    subprocess.run(["python", "fetch_tax_data.py"])

    # Initialize database with sample data if needed
    db = next(get_db())
    
    # Initialize tax data
    try:
        scraper = SARSDataScraper()
        current_tax_year = get_tax_year()
        
        try:
            # First try to get current tax year data
            await scraper.update_tax_data(db)
            print(f"Successfully initialized tax data for {current_tax_year}")
        except Exception as e:
            print(f"Could not retrieve current tax year data: {e}")
            print("Falling back to previous tax year data...")
            
            # If current year fails, try previous tax year
            previous_year_start = int(current_tax_year.split('-')[0]) - 1
            previous_year_end = int(current_tax_year.split('-')[1]) - 1
            previous_tax_year = f"{previous_year_start}-{previous_year_end}"
            
            # Check if we already have data for the previous year
            existing = db.query(TaxBracket).filter(TaxBracket.tax_year == previous_tax_year).first()
            
            if existing:
                print(f"Using existing {previous_tax_year} tax data")
                # Copy previous year data to current year
                await copy_tax_year_data(db, previous_tax_year, current_tax_year)
            else:
                # Try to scrape previous year data
                try:
                    await scraper.update_tax_data(db, previous_tax_year)
                    await copy_tax_year_data(db, previous_tax_year, current_tax_year)
                except Exception as e2:
                    print(f"Could not retrieve previous tax year data: {e2}")
                    print("Falling back to manual tax data entry...")
                    # Use the manual seed function from seed_data.py
                    from scripts.seed_data import seed_tax_data_manually
                    await seed_tax_data_manually(db, current_tax_year)
    except Exception as e:
        print(f"Error initializing tax data: {e}")
    
    db.close()

async def copy_tax_year_data(db: Session, source_year: str, target_year: str):
    """Copy tax data from one year to another when SARS hasn't updated yet."""
    print(f"Copying tax data from {source_year} to {target_year}...")
    
    # Get source year tax brackets
    brackets = db.query(TaxBracket).filter(TaxBracket.tax_year == source_year).all()
    rebate = db.query(TaxRebate).filter(TaxRebate.tax_year == source_year).first()
    threshold = db.query(TaxThreshold).filter(TaxThreshold.tax_year == source_year).first()
    medical = db.query(MedicalTaxCredit).filter(MedicalTaxCredit.tax_year == source_year).first()
    
    # Clear any existing data for target year
    db.query(TaxBracket).filter(TaxBracket.tax_year == target_year).delete()
    db.query(TaxRebate).filter(TaxRebate.tax_year == target_year).delete()
    db.query(TaxThreshold).filter(TaxThreshold.tax_year == target_year).delete()
    db.query(MedicalTaxCredit).filter(MedicalTaxCredit.tax_year == target_year).delete()
    
    # Copy brackets with new tax year
    for bracket in brackets:
        new_bracket = TaxBracket(
            lower_limit=bracket.lower_limit,
            upper_limit=bracket.upper_limit,
            rate=bracket.rate,
            base_amount=bracket.base_amount,
            tax_year=target_year
        )
        db.add(new_bracket)
    
    # Copy rebate
    if rebate:
        new_rebate = TaxRebate(
            primary=rebate.primary,
            secondary=rebate.secondary,
            tertiary=rebate.tertiary,
            tax_year=target_year
        )
        db.add(new_rebate)
    
    # Copy threshold
    if threshold:
        new_threshold = TaxThreshold(
            below_65=threshold.below_65,
            age_65_to_74=threshold.age_65_to_74,
            age_75_plus=threshold.age_75_plus,
            tax_year=target_year
        )
        db.add(new_threshold)
    
    # Copy medical credits
    if medical:
        new_medical = MedicalTaxCredit(
            main_member=medical.main_member,
            additional_member=medical.additional_member,
            tax_year=target_year
        )
        db.add(new_medical)
    
    # Commit all changes
    db.commit()
    print(f"Successfully copied tax data from {source_year} to {target_year}")
    
    db.close()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

def run_app():
    """Entry point for the application when used as a package."""
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)