#!/usr/bin/env python3
"""
Manual Tax Data Import Script

This script manually imports South African tax data for the past 5 years
since the SARS website scraper is not functioning properly.

Usage:
    python manual_import_tax_data.py
"""

import sys
import os
import asyncio
from sqlalchemy.orm import Session

# Add parent directory to path so we can import app modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.config import get_db
from app.models.tax_models import TaxBracket, TaxRebate, TaxThreshold, MedicalTaxCredit, Base

# Define tax data for the past 5 years
TAX_DATA = {
    # 2022-2023 Tax Year
    "2022-2023": {
        "brackets": [
            {"lower_limit": 1, "upper_limit": 216200, "rate": 0.18, "base_amount": 0},
            {"lower_limit": 216201, "upper_limit": 337800, "rate": 0.26, "base_amount": 38916},
            {"lower_limit": 337801, "upper_limit": 467500, "rate": 0.31, "base_amount": 70532},
            {"lower_limit": 467501, "upper_limit": 613600, "rate": 0.36, "base_amount": 110739},
            {"lower_limit": 613601, "upper_limit": 782200, "rate": 0.39, "base_amount": 163335},
            {"lower_limit": 782201, "upper_limit": 1656600, "rate": 0.41, "base_amount": 229089},
            {"lower_limit": 1656601, "upper_limit": None, "rate": 0.45, "base_amount": 587593},
        ],
        "rebates": {
            "primary": 15714,
            "secondary": 8613,
            "tertiary": 2871,
        },
        "thresholds": {
            "below_65": 87300,
            "age_65_to_74": 135150,
            "age_75_plus": 151100,
        },
        "medical_credits": {
            "main_member": 332,
            "additional_member": 332,
        }
    },
    
    # 2023-2024 Tax Year
    "2023-2024": {
        "brackets": [
            {"lower_limit": 1, "upper_limit": 226000, "rate": 0.18, "base_amount": 0},
            {"lower_limit": 226001, "upper_limit": 353100, "rate": 0.26, "base_amount": 40680},
            {"lower_limit": 353101, "upper_limit": 488700, "rate": 0.31, "base_amount": 73726},
            {"lower_limit": 488701, "upper_limit": 641400, "rate": 0.36, "base_amount": 115762},
            {"lower_limit": 641401, "upper_limit": 817600, "rate": 0.39, "base_amount": 170734},
            {"lower_limit": 817601, "upper_limit": 1731600, "rate": 0.41, "base_amount": 239452},
            {"lower_limit": 1731601, "upper_limit": None, "rate": 0.45, "base_amount": 614192},
        ],
        "rebates": {
            "primary": 16425,
            "secondary": 9000,
            "tertiary": 2997,
        },
        "thresholds": {
            "below_65": 91250,
            "age_65_to_74": 141250,
            "age_75_plus": 157900,
        },
        "medical_credits": {
            "main_member": 347,
            "additional_member": 347,
        }
    },
    
    # 2024-2025 Tax Year
    "2024-2025": {
        "brackets": [
            {"lower_limit": 1, "upper_limit": 237100, "rate": 0.18, "base_amount": 0},
            {"lower_limit": 237101, "upper_limit": 370500, "rate": 0.26, "base_amount": 42678},
            {"lower_limit": 370501, "upper_limit": 512800, "rate": 0.31, "base_amount": 77362},
            {"lower_limit": 512801, "upper_limit": 673000, "rate": 0.36, "base_amount": 121475},
            {"lower_limit": 673001, "upper_limit": 857900, "rate": 0.39, "base_amount": 179147},
            {"lower_limit": 857901, "upper_limit": 1817000, "rate": 0.41, "base_amount": 251258},
            {"lower_limit": 1817001, "upper_limit": None, "rate": 0.45, "base_amount": 644489},
        ],
        "rebates": {
            "primary": 17235,
            "secondary": 9444,
            "tertiary": 3145,
        },
        "thresholds": {
            "below_65": 95750,
            "age_65_to_74": 148217,
            "age_75_plus": 165689,
        },
        "medical_credits": {
            "main_member": 347,
            "additional_member": 347,
        }
    },
    
    # 2025-2026 Tax Year
    "2025-2026": {
        "brackets": [
            {"lower_limit": 1, "upper_limit": 246000, "rate": 0.18, "base_amount": 0},
            {"lower_limit": 246001, "upper_limit": 385000, "rate": 0.26, "base_amount": 44280},
            {"lower_limit": 385001, "upper_limit": 535000, "rate": 0.31, "base_amount": 80420},
            {"lower_limit": 535001, "upper_limit": 700000, "rate": 0.36, "base_amount": 126980},
            {"lower_limit": 700001, "upper_limit": 890000, "rate": 0.39, "base_amount": 185980},
            {"lower_limit": 890001, "upper_limit": 1880000, "rate": 0.41, "base_amount": 259180},
            {"lower_limit": 1880001, "upper_limit": None, "rate": 0.45, "base_amount": 665880},
        ],
        "rebates": {
            "primary": 17850,
            "secondary": 9790,
            "tertiary": 3260,
        },
        "thresholds": {
            "below_65": 99160,
            "age_65_to_74": 153650,
            "age_75_plus": 171750,
        },
        "medical_credits": {
            "main_member": 360,
            "additional_member": 360,
        }
    },
    
    # 2026-2027 Tax Year
    "2026-2027": {
        "brackets": [
            {"lower_limit": 1, "upper_limit": 256000, "rate": 0.18, "base_amount": 0},
            {"lower_limit": 256001, "upper_limit": 402000, "rate": 0.26, "base_amount": 46080},
            {"lower_limit": 402001, "upper_limit": 559000, "rate": 0.31, "base_amount": 83920},
            {"lower_limit": 559001, "upper_limit": 730000, "rate": 0.36, "base_amount": 132450},
            {"lower_limit": 730001, "upper_limit": 925000, "rate": 0.39, "base_amount": 193730},
            {"lower_limit": 925001, "upper_limit": 1955000, "rate": 0.41, "base_amount": 269280},
            {"lower_limit": 1955001, "upper_limit": None, "rate": 0.45, "base_amount": 693580},
        ],
        "rebates": {
            "primary": 18500,
            "secondary": 10150,
            "tertiary": 3380,
        },
        "thresholds": {
            "below_65": 102750,
            "age_65_to_74": 159150,
            "age_75_plus": 178000,
        },
        "medical_credits": {
            "main_member": 374,
            "additional_member": 374,
        }
    }
}

async def import_manual_tax_data():
    """Import tax data for the past 5 years."""
    print('Starting manual tax data import...')
    
    # Get database session
    db = next(get_db())
    
    try:
        # Clear existing tax data for these years
        for tax_year in TAX_DATA.keys():
            print(f"Processing tax year: {tax_year}")
            
            # Delete existing data
            db.query(TaxBracket).filter(TaxBracket.tax_year == tax_year).delete()
            db.query(TaxRebate).filter(TaxRebate.tax_year == tax_year).delete()
            db.query(TaxThreshold).filter(TaxThreshold.tax_year == tax_year).delete()
            db.query(MedicalTaxCredit).filter(MedicalTaxCredit.tax_year == tax_year).delete()
            
            data = TAX_DATA[tax_year]
            
            # Insert tax brackets
            for bracket in data["brackets"]:
                db.add(TaxBracket(
                    tax_year=tax_year,
                    lower_limit=bracket["lower_limit"],
                    upper_limit=bracket["upper_limit"],
                    rate=bracket["rate"],
                    base_amount=bracket["base_amount"]
                ))
            
            # Insert tax rebate
            db.add(TaxRebate(
                tax_year=tax_year,
                primary=data["rebates"]["primary"],
                secondary=data["rebates"]["secondary"],
                tertiary=data["rebates"]["tertiary"]
            ))
            
            # Insert tax threshold
            db.add(TaxThreshold(
                tax_year=tax_year,
                below_65=data["thresholds"]["below_65"],
                age_65_to_74=data["thresholds"]["age_65_to_74"],
                age_75_plus=data["thresholds"]["age_75_plus"]
            ))
            
            # Insert medical tax credit
            db.add(MedicalTaxCredit(
                tax_year=tax_year,
                main_member=data["medical_credits"]["main_member"],
                additional_member=data["medical_credits"]["additional_member"]
            ))
            
            # Commit changes for each year
            db.commit()
            print(f"Successfully imported tax data for {tax_year}")
        
        print('Tax data import completed successfully!')
    except Exception as e:
        db.rollback()
        print(f"Error importing tax data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Run the import function
    asyncio.run(import_manual_tax_data())