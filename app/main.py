# app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy.orm import Session

from app.core.config import settings, get_db, engine
from app.models.tax_models import Base
from app.api.routes import tax_calculator
from app.core.data_scraper import SARSDataScraper

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
    # Initialize database with sample data if needed
    db = next(get_db())
    
    # Initialize tax data
    try:
        scraper = SARSDataScraper()
        await scraper.update_tax_data(db)
    except Exception as e:
        print(f"Error initializing tax data: {e}")
    
    db.close()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

def run_app():
    """Entry point for the application when used as a package."""
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)