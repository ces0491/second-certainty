# Installation Guide

This guide provides detailed instructions for setting up the Second Certainty Tax Management System for local development.

## Prerequisites

Before you begin, ensure you have the following:

- **Python 3.10+** - Required for the backend
- **Node.js 16+** - Required for the frontend  
- **PostgreSQL** (optional) - For production-like development, or SQLite for simpler setup
- **Git** - For version control

## Backend Setup

### 1. Clone the Repository

```bash
git clone https://github.com/ces0491/second-certainty.git
cd second-certainty
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp env.example .env
```

Edit the `.env` file with your configuration:

```bash
# Database Configuration
# For development (SQLite) - Default option
DATABASE_URL=sqlite:///./second_certainty.db

# For production (PostgreSQL) - Uncomment and configure
# DATABASE_URL=postgresql://username:password@localhost:5432/second_certainty

# Security Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 1 week

# Application Configuration
APP_NAME="Second Certainty"
APP_VERSION="1.0.0"
API_PREFIX="/api"
DEBUG=True
ENVIRONMENT=development

# SARS Configuration
SARS_WEBSITE_URL=https://www.sars.gov.za

# CORS Configuration
CORS_ORIGINS=http://localhost:3000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
ENABLE_QUERY_LOGGING=False
SLOW_QUERY_THRESHOLD=1.0

# File Upload Configuration
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=uploads
ALLOWED_FILE_TYPES=.pdf,.jpg,.jpeg,.png

# Rate Limiting
ENABLE_RATE_LIMITING=True
DEFAULT_RATE_LIMIT=100
AUTH_RATE_LIMIT=5

# Scraping Configuration
SCRAPING_TIMEOUT=30
SCRAPING_RETRIES=3
```

For a secure `SECRET_KEY`, you can generate one with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Set Up the Database

#### Using SQLite (Recommended for Development)

SQLite is the default and simplest option for development:

```bash
# Initialize database and create tables
python init_db.py

# Seed the database with initial data
python scripts/seed_data.py
```

#### Using PostgreSQL (Production-like Setup)

If you prefer PostgreSQL for development:

1. Install PostgreSQL and create a database:

```bash
# On Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# On macOS with Homebrew
brew install postgresql
brew services start postgresql

# Create database and user
sudo -u postgres psql
CREATE DATABASE second_certainty;
CREATE USER second_certainty_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE second_certainty TO second_certainty_user;
\q
```

2. Update the `DATABASE_URL` in your `.env` file:

```bash
DATABASE_URL=postgresql://second_certainty_user:your_password@localhost:5432/second_certainty
```

3. Initialize the database:

```bash
python init_db.py
python scripts/seed_data.py
```

### 6. Run Database Migrations (if needed)

If you're working with an existing database or need to apply schema changes:

```bash
# Check current migration status
alembic current

# Apply any pending migrations
alembic upgrade head
```

### 7. Create an Admin Account

To create an admin account for accessing administrative features:

```bash
python create_admin.py your_email@example.com secure_password Your Name Surname
```

### 8. Start the Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **Main API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/api/health

## Frontend Setup

### 1. Clone the Frontend Repository

```bash
git clone https://github.com/ces0491/second-certainty-frontend.git
cd second-certainty-frontend
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment Variables

Create a `.env.local` file:

```bash
REACT_APP_API_BASE_URL=http://localhost:8000/api
```

### 4. Start the Development Server

```bash
npm start
```

The frontend will be available at http://localhost:3000.

## Working with the Full Stack

For the best development experience, run both servers simultaneously:

### Terminal 1 (Backend):
```bash
cd /path/to/second-certainty
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload
```

### Terminal 2 (Frontend):
```bash
cd /path/to/second-certainty-frontend
npm start
```

## Testing the Installation

### 1. Test Backend Health

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "version": "1.0.0",
  "database": {
    "status": "healthy",
    "error": null
  }
}
```

### 2. Test User Registration

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "name": "Test",
    "surname": "User",
    "date_of_birth": "1990-01-01",
    "is_provisional_taxpayer": false
  }'
```

### 3. Test Frontend Connection

Open http://localhost:3000 in your browser and verify:
- The application loads without errors
- You can navigate to the registration page
- The registration form submits successfully

## Development Tools

### Database Management

```bash
# List all users
python list_users.py

# Debug a specific user
python debug_user_profile.py <user_id>

# Update tax data manually
python fetch_tax_data.py --year 2024-2025 --force

# Create additional admin users
python create_admin.py admin2@example.com password123 Admin Two
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Add new field to user model"

# Apply migrations
alembic upgrade head

# Rollback to previous migration
alembic downgrade -1

# View migration history
alembic history
```

### Code Quality

```bash
# Format code with Black
black app/

# Sort imports
isort app/

# Lint code
flake8 app/
```

## Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_api/test_tax_calculator.py

# Run tests with verbose output
pytest -v

# Run async tests
pytest tests/test_core/test_data_scraper.py -v
```

### Frontend Tests

```bash
cd second-certainty-frontend

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

## Troubleshooting

### Common Backend Issues

#### Database Connection Errors
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# Test database connection
python -c "
from app.core.config import get_db
db = next(get_db())
print('Database connection successful')
db.close()
"
```

#### Import Errors
```bash
# Ensure virtual environment is activated
which python  # Should point to your venv

# Reinstall requirements
pip install --upgrade -r requirements.txt
```

#### Port Already in Use
```bash
# Kill process using port 8000
sudo lsof -ti:8000 | xargs kill -9

# Use a different port
uvicorn app.main:app --reload --port 8001
```

#### Missing Environment Variables
```bash
# Check if .env file exists and is readable
ls -la .env
cat .env

# Verify environment variables are loaded
python -c "
from app.core.config import settings
print(f'Database URL: {settings.DATABASE_URL}')
print(f'Secret Key: {settings.SECRET_KEY[:10]}...')
"
```

### Common Frontend Issues

#### API Connection Errors
```bash
# Verify backend is running
curl http://localhost:8000/api/health

# Check CORS configuration
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     http://localhost:8000/api/health
```

#### Node Module Errors
```bash
# Clear npm cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

#### Build Errors
```bash
# Check for TypeScript errors
npm run build

# Verify environment variables
echo $REACT_APP_API_BASE_URL
```

### Logging and Debugging

#### Enable Debug Logging
In your `.env` file:
```bash
DEBUG=True
LOG_LEVEL=DEBUG
ENABLE_QUERY_LOGGING=True
```

#### Check Log Files
```bash
# View application logs
tail -f logs/second_certainty.log

# View error logs
tail -f logs/second_certainty_error.log
```

#### Debug Database Issues
```bash
# Check database tables
python -c "
from app.core.config import engine
from sqlalchemy import inspect
inspector = inspect(engine)
print('Tables:', inspector.get_table_names())
"

# Check if seed data exists
python -c "
from app.core.config import get_db
from app.models.tax_models import TaxBracket
db = next(get_db())
count = db.query(TaxBracket).count()
print(f'Tax brackets in database: {count}')
db.close()
"
```

## Next Steps

After successful installation:

1. **Create a test user account** via the frontend registration page
2. **Add sample income and expenses** to test calculations
3. **Explore the tax calculation features**
4. **Review the API documentation** at http://localhost:8000/api/docs
5. **Check the admin features** if you created an admin account

For production deployment, see the [Deployment Guide](./DEPLOYMENT.md).