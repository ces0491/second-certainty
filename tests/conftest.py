# tests/conftest.py
import os
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test_second_certainty.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

from app.core.auth import create_access_token, get_password_hash
from app.core.config import get_db
from app.main import app
from app.models.tax_models import (
    Base,
    DeductibleExpenseType,
    MedicalTaxCredit,
    TaxBracket,
    TaxRebate,
    TaxThreshold,
    UserProfile,
)
from app.utils.tax_utils import get_tax_year

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_second_certainty.db"


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    yield db

    # Cleanup
    db.close()
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user(test_db):
    """Create test user."""
    user = UserProfile(
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        name="Test",
        surname="User",
        date_of_birth=date(1990, 5, 15),
        is_provisional_taxpayer=True,
        is_admin=False,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def admin_user(test_db):
    """Create admin user."""
    user = UserProfile(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        name="Admin",
        surname="User",
        date_of_birth=date(1985, 3, 10),
        is_provisional_taxpayer=False,
        is_admin=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create auth headers for test user."""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user):
    """Create auth headers for admin user."""
    token = create_access_token(data={"sub": admin_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def complete_tax_data(test_db):
    """Set up complete tax data for testing."""
    tax_year = get_tax_year()

    # Clear any existing data first to prevent constraint violations
    test_db.query(TaxBracket).filter(TaxBracket.tax_year == tax_year).delete()
    test_db.query(TaxRebate).filter(TaxRebate.tax_year == tax_year).delete()
    test_db.query(TaxThreshold).filter(TaxThreshold.tax_year == tax_year).delete()
    test_db.query(MedicalTaxCredit).filter(MedicalTaxCredit.tax_year == tax_year).delete()
    test_db.query(DeductibleExpenseType).delete()  # Clear all expense types
    test_db.commit()

    # Tax brackets - 2024-2025 South African tax brackets
    brackets = [
        {"lower_limit": 1, "upper_limit": 237100, "rate": 0.18, "base_amount": 0, "tax_year": tax_year},
        {"lower_limit": 237101, "upper_limit": 370500, "rate": 0.26, "base_amount": 42678, "tax_year": tax_year},
        {"lower_limit": 370501, "upper_limit": 512800, "rate": 0.31, "base_amount": 77362, "tax_year": tax_year},
        {"lower_limit": 512801, "upper_limit": 673000, "rate": 0.36, "base_amount": 121475, "tax_year": tax_year},
        {"lower_limit": 673001, "upper_limit": 857900, "rate": 0.39, "base_amount": 179147, "tax_year": tax_year},
        {"lower_limit": 857901, "upper_limit": 1817000, "rate": 0.41, "base_amount": 251258, "tax_year": tax_year},
        {"lower_limit": 1817001, "upper_limit": None, "rate": 0.45, "base_amount": 644489, "tax_year": tax_year},
    ]

    for bracket_data in brackets:
        test_db.add(TaxBracket(**bracket_data))

    # Tax rebates - 2024-2025 values
    rebate = TaxRebate(
        primary=17235,  # Primary rebate (all taxpayers)
        secondary=9444,  # Secondary rebate (65+ years)
        tertiary=3145,  # Tertiary rebate (75+ years)
        tax_year=tax_year,
    )
    test_db.add(rebate)

    # Tax thresholds - 2024-2025 values
    threshold = TaxThreshold(
        below_65=95750,  # Tax threshold for under 65
        age_65_to_74=148217,  # Tax threshold for 65-74
        age_75_plus=165689,  # Tax threshold for 75+
        tax_year=tax_year,
    )
    test_db.add(threshold)

    # Medical tax credits - 2024-2025 values
    medical = MedicalTaxCredit(
        main_member=347,  # Monthly credit for main member
        additional_member=347,  # Monthly credit for each additional member
        tax_year=tax_year,
    )
    test_db.add(medical)

    # Deductible expense types - use unique names to avoid constraint violations
    expense_types = [
        {
            "name": "Test Retirement Annuity",
            "description": "Retirement annuity contributions for testing",
            "max_percentage": 27.5,  # 27.5% of income or R350,000
            "max_deduction": 350000,
            "is_active": True,
        },
        {
            "name": "Test Medical Expenses",
            "description": "Out of pocket medical expenses for testing",
            "max_percentage": None,
            "max_deduction": None,
            "is_active": True,
        },
        {
            "name": "Test Donations",
            "description": "Donations to Public Benefit Organizations for testing",
            "max_percentage": 10.0,  # 10% of taxable income
            "max_deduction": None,
            "is_active": True,
        },
    ]

    for expense_data in expense_types:
        test_db.add(DeductibleExpenseType(**expense_data))

    test_db.commit()
    
    print("Deductible expense types seeded successfully.")
    return tax_year


@pytest.fixture
def sample_income_data():
    """Sample income data for testing."""
    return {
        "source_type": "Salary",
        "description": "Monthly salary from employer",
        "annual_amount": 350000,
        "is_paye": True,
    }


@pytest.fixture
def sample_expense_data():
    """Sample expense data for testing."""
    return {"expense_type_id": 1, "description": "Monthly retirement annuity contribution", "amount": 5000}


@pytest.fixture
def sample_user_data():
    """Sample user registration data."""
    return {
        "email": "newuser@test.com",
        "password": "strongpass123",
        "name": "New",
        "surname": "User",
        "date_of_birth": "1992-06-20",
        "is_provisional_taxpayer": False,
    }
