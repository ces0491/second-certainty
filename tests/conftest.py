# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import date

from app.core.auth import create_access_token
from app.core.config import get_db
from app.main import app
from app.models.tax_models import Base, UserProfile, TaxBracket, TaxRebate, TaxThreshold, MedicalTaxCredit, DeductibleExpenseType
from app.utils.tax_utils import get_tax_year

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create the tables
    Base.metadata.create_all(bind=engine)

    # Use our test database instead of the real one
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Create a db session for the tests to use
    db = TestingSessionLocal()

    yield db  # This is where the testing happens

    # Cleanup after tests
    db.close()
    Base.metadata.drop_all(bind=engine)
    # Clear dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client for the API."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user(test_db):
    """Create a test user for authentication tests."""
    from app.core.auth import get_password_hash

    # Create a test user
    user = UserProfile(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        name="Test",
        surname="User", 
        date_of_birth=date(1990, 1, 1),
        is_provisional_taxpayer=True,
        is_admin=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    return user


@pytest.fixture
def test_admin_user(test_db):
    """Create a test admin user."""
    from app.core.auth import get_password_hash

    user = UserProfile(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        name="Admin",
        surname="User",
        date_of_birth=date(1985, 1, 1),
        is_provisional_taxpayer=False,
        is_admin=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    return user


@pytest.fixture
def token(test_user):
    """Create a valid token for the test user."""
    return create_access_token(data={"sub": test_user.email})


@pytest.fixture
def admin_token(test_admin_user):
    """Create a valid token for the admin user."""
    return create_access_token(data={"sub": test_admin_user.email})


@pytest.fixture
def authorized_client(client, token):
    """Create a client with authorization headers."""
    client.headers = {**client.headers, "Authorization": f"Bearer {token}"}
    return client


@pytest.fixture
def admin_client(client, admin_token):
    """Create a client with admin authorization headers."""
    client.headers = {**client.headers, "Authorization": f"Bearer {admin_token}"}
    return client


@pytest.fixture
def tax_data_setup(test_db):
    """Set up basic tax data for testing."""
    tax_year = get_tax_year()
    
    # Create tax brackets
    brackets_data = [
        {"lower_limit": 1, "upper_limit": 237100, "rate": 0.18, "base_amount": 0, "tax_year": tax_year},
        {"lower_limit": 237101, "upper_limit": 370500, "rate": 0.26, "base_amount": 42678, "tax_year": tax_year},
        {"lower_limit": 370501, "upper_limit": 512800, "rate": 0.31, "base_amount": 77362, "tax_year": tax_year},
        {"lower_limit": 512801, "upper_limit": 673000, "rate": 0.36, "base_amount": 121475, "tax_year": tax_year},
        {"lower_limit": 673001, "upper_limit": 857900, "rate": 0.39, "base_amount": 179147, "tax_year": tax_year},
        {"lower_limit": 857901, "upper_limit": 1817000, "rate": 0.41, "base_amount": 251258, "tax_year": tax_year},
        {"lower_limit": 1817001, "upper_limit": None, "rate": 0.45, "base_amount": 644489, "tax_year": tax_year},
    ]
    
    for bracket_data in brackets_data:
        bracket = TaxBracket(**bracket_data)
        test_db.add(bracket)
    
    # Create tax rebate
    rebate = TaxRebate(
        primary=17235,
        secondary=9444,
        tertiary=3145,
        tax_year=tax_year
    )
    test_db.add(rebate)
    
    # Create tax threshold
    threshold = TaxThreshold(
        below_65=95750,
        age_65_to_74=148217,
        age_75_plus=165689,
        tax_year=tax_year
    )
    test_db.add(threshold)
    
    # Create medical credit
    medical = MedicalTaxCredit(
        main_member=347,
        additional_member=347,
        tax_year=tax_year
    )
    test_db.add(medical)
    
    test_db.commit()
    
    return {
        "tax_year": tax_year,
        "brackets": brackets_data,
        "rebate": rebate,
        "threshold": threshold,
        "medical": medical
    }


@pytest.fixture
def expense_types_setup(test_db):
    """Set up deductible expense types for testing."""
    expense_types = [
        {
            "name": "Retirement Annuity Contributions",
            "description": "Contributions to retirement annuities",
            "max_percentage": 27.5,
            "max_deduction": 350000,
            "is_active": True,
        },
        {
            "name": "Medical Expenses",
            "description": "Out-of-pocket medical expenses",
            "max_percentage": None,
            "max_deduction": None,
            "is_active": True,
        },
        {
            "name": "Donations",
            "description": "Donations to PBOs",
            "max_percentage": 10,
            "max_deduction": None,
            "is_active": True,
        },
    ]
    
    for expense_data in expense_types:
        expense_type = DeductibleExpenseType(**expense_data)
        test_db.add(expense_type)
    
    test_db.commit()
    
    return expense_types


@pytest.fixture
def mock_tax_brackets():
    """Fixture providing test tax brackets for calculations."""
    return [
        {"lower_limit": 1, "upper_limit": 237100, "rate": 0.18, "base_amount": 0},
        {"lower_limit": 237101, "upper_limit": 370500, "rate": 0.26, "base_amount": 42678},
        {"lower_limit": 370501, "upper_limit": 512800, "rate": 0.31, "base_amount": 77362},
        {"lower_limit": 512801, "upper_limit": 673000, "rate": 0.36, "base_amount": 121475},
        {"lower_limit": 673001, "upper_limit": 857900, "rate": 0.39, "base_amount": 179147},
        {"lower_limit": 857901, "upper_limit": 1817000, "rate": 0.41, "base_amount": 251258},
        {"lower_limit": 1817001, "upper_limit": None, "rate": 0.45, "base_amount": 644489}
    ]


@pytest.fixture
def sample_user_data():
    """Fixture for test user data."""
    return {
        "email": "newuser@example.com",
        "password": "testpassword123",
        "name": "New",
        "surname": "User",
        "date_of_birth": "1995-05-15",
        "is_provisional_taxpayer": False
    }