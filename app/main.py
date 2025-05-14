# app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy.orm import Session
import logging
import os
from pathlib import Path
from scripts.seed_data import initialize_database

from app.core.config import settings, get_db, engine
from app.models.tax_models import Base
from app.api.routes import tax_calculator
from app.core.data_scraper import SARSDataScraper
from app.models.tax_models import TaxBracket, TaxRebate, TaxThreshold, MedicalTaxCredit
from app.utils.tax_utils import get_tax_year
from app.api.routes import admin
from app.utils.logging_utils import setup_logging, get_logger

# Set up application logging
logger = setup_logging(
    app_name="second_certainty",
    log_level=logging.DEBUG if settings.DEBUG else logging.INFO
)

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
    allow_origins=["https://second-certainty-frontend.onrender.com"],  # production frontend domain
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
    logger.info("Root endpoint accessed")
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "Welcome to the Second Certainty Tax API"
    }

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.
    Handles startup and shutdown events.
    """
    # STARTUP
    logger.info("Application starting up")
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Initialize database with seed data if needed
    db = next(get_db())
    
    try:
        from scripts.seed_data import initialize_database
        await initialize_database(db)
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
    finally:
        db.close()
    
    logger.info("Application startup complete")
    
    yield  # This is where the application runs
    
    # SHUTDOWN
    logger.info("Application shutting down")

# Then create the app with the lifespan parameter
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="South African tax liability management API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

def run_app():
    """Entry point for the application when used as a package."""
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)