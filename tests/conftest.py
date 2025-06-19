#tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import create_access_token
from app.core.config import get_db
from app.main import app
from app.models.tax_models import Base
import pytest
from decimal import Decimal

@pytest.fixture
def mock_tax_brackets():
    """Fixture providing test tax brackets for 2025-2026"""
    return [
        {"min_income": 0, "max_income": 237100, "rate": 0.18, "base_tax": 0},
        {"min_income": 237101, "max_income": 370500, "rate": 0.26, "base_tax": 42678},
        {"min_income": 370501, "max_income": 512800, "rate": 0.31, "base_tax": 77362},
        {"min_income": 512801, "max_income": 673000, "rate": 0.36, "base_tax": 121475},
        {"min_income": 673001, "max_income": 857900, "rate": 0.39, "base_tax": 179147},
        {"min_income": 857901, "max_income": 1817000, "rate": 0.41, "base_tax": 251258},
        {"min_income": 1817001, "max_income": float('inf'), "rate": 0.45, "base_tax": 644489}
    ]

@pytest.fixture
def sample_user_data():
    """Fixture for test user data"""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "name": "Test",
        "surname": "User",
        "id_number": "9001010001080",
        "date_of_birth": "1990-01-01"
    }

#Create an in-memory SQLite database for testing
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

    #Create the tables
    Base.metadata.create_all(bind=engine)

    #Use our test database instead of the real one
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    #Create a db session for the tests to use
    db = TestingSessionLocal()

    yield db  #This is where the testing happens

    #Cleanup after tests
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client for the API."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user(test_db):
    """Create a test user for authentication tests."""
    from datetime import date

    from app.core.auth import get_password_hash
    from app.models.tax_models import UserProfile

    #Create a test user
    user = UserProfile(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        name="Test",
        surname="User",
        date_of_birth=date(1990, 1, 1),
        is_provisional_taxpayer=True,
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
def authorized_client(client, token):
    """Create a client with authorization headers."""
    client.headers = {**client.headers, "Authorization": f"Bearer {token}"}
    return client
