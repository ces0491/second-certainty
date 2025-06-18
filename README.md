# Second Certainty - Tax Management System

A comprehensive South African tax liability management system that helps users track, calculate, and optimize their tax obligations throughout the fiscal year.

![*logo generated using OpenAI's DALL·E model via ChatGPT (May 2025)](docs/images/sc_logo.png)

## Live Demo

- **Frontend Application**: [https://second-certainty.onrender.com](https://second-certainty.onrender.com)
- **Backend API**: [https://second-certainty-api.onrender.com](https://second-certainty-api.onrender.com)
- **API Documentation**: [https://second-certainty-api.onrender.com/api/docs](https://second-certainty-api.onrender.com/api/docs)
- **Frontend Repository**: [https://github.com/ces0491/second-certainty-frontend](https://github.com/ces0491/second-certainty-frontend)

> **Note**: The application is deployed on Render's free tier, which may result in slow initial load times after periods of inactivity. When logging in, please note that you may need to retry after `No response from server` message - this is a function of deployment on Render's free tier.

## Overview

The Second Certainty Tax Tool addresses one of life's two certainties—taxes—by providing individuals and small businesses with an intuitive platform for managing tax liabilities throughout the fiscal year. Traditional tax management often occurs reactively at year-end, leading to unexpected liabilities, missed deductions, and financial stress.

Our application transforms this approach by implementing a proactive, year-round tax management system that continuously calculates estimated tax liabilities based on income streams, identifies potential deductions, forecasts provisional payments, and provides optimization strategies—all in real-time.

## Features

### Core Functionality
- **User Authentication**: Secure JWT-based authentication system with HTTPBearer tokens
- **Profile Management**: Create and manage user tax profiles with provisional taxpayer status
- **Income Tracking**: Log multiple income sources (salary, freelance, investments, etc.)
- **Expense Management**: Record and categorize tax-deductible expenses with predefined types
- **Real-time Tax Calculation**: Calculate current tax position at any time
- **Provisional Tax**: Calculate and track provisional tax payments for eligible taxpayers

### Tax Data Management
- **Up-to-date Tax Information**: Current tax brackets, rebates, thresholds for South Africa
- **SARS Integration**: Automatic scraping of latest tax rates from SARS website with multiple fallback strategies
- **Historical Data**: Support for multiple tax years with automatic tax year detection
- **Manual Data Entry**: Fallback to manual tax data when scraping fails

### Advanced Features
- **Data Validation**: Comprehensive input validation and error handling
- **Database Migrations**: Alembic-powered database schema management
- **Background Tasks**: Asynchronous tax data updates
- **Admin Features**: Administrative endpoints for tax data management
- **Comprehensive Logging**: Structured logging with file rotation

## Technology Stack

### Backend
- **Framework**: FastAPI 0.110.1
- **ORM**: SQLAlchemy 2.0.40
- **Validation**: Pydantic 2.6.0 with pydantic-settings 2.2.1
- **Database**: PostgreSQL (production), SQLite (development)
- **Authentication**: JWT with python-jose[cryptography] 3.3.0 and passlib[bcrypt] 1.7.4
- **Testing**: Pytest 7.4.4 with pytest-asyncio 0.23.5
- **Documentation**: OpenAPI (Swagger UI)
- **HTTP Client**: HTTPX 0.27.0 for async web scraping
- **Server**: Uvicorn 0.29.0
- **Web Scraping**: BeautifulSoup4 4.12.3 with lxml 5.1.0
- **Database Migrations**: Alembic 1.13.1

### Frontend
- **Framework**: React 18.2
- **Routing**: React Router 6.22.1
- **HTTP Client**: Axios 1.6.7
- **State Management**: React Context API
- **Styling**: Tailwind CSS 3.4.1
- **Data Visualization**: Recharts 2.12.0
- **Build Tools**: Create React App

### Development Tools
- **Code Formatting**: Black 24.2.0, isort 5.13.2
- **Linting**: Flake8 7.0.0
- **Environment**: python-dotenv 1.0.1

## Quick Start

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/ces0491/second-certainty.git
cd second-certainty

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp env.example .env
# Edit .env with your configuration (see Environment Variables section)

# Initialize database
python init_db.py

# Seed initial data
python scripts/seed_data.py

# Start development server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
# Clone frontend repository
git clone https://github.com/ces0491/second-certainty-frontend.git
cd second-certainty-frontend

# Install dependencies
npm install

# Create environment file
echo "REACT_APP_API_BASE_URL=http://localhost:8000/api" > .env.local

# Start development server
npm start
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Database Configuration
DATABASE_URL=sqlite:///./second_certainty.db  # For development
# DATABASE_URL=postgresql://username:password@localhost:5432/second_certainty  # For production

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

# File Upload Configuration
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=uploads
ALLOWED_FILE_TYPES=.pdf,.jpg,.jpeg,.png

# Rate Limiting
ENABLE_RATE_LIMITING=True
DEFAULT_RATE_LIMIT=100
AUTH_RATE_LIMIT=5
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login with email/password (JSON)
- `POST /api/auth/token` - OAuth2 compatible login
- `GET /api/auth/me` - Get current user profile
- `PUT /api/auth/profile` - Update user profile
- `PUT /api/auth/change-password` - Change password
- `POST /api/auth/logout` - Logout endpoint

### Tax Management
- `GET /api/tax/tax-brackets/` - Get tax brackets for tax year
- `GET /api/tax/deductible-expenses/` - Get deductible expense types
- `POST /api/tax/users/{user_id}/income/` - Add income source
- `GET /api/tax/users/{user_id}/income/` - Get user income sources
- `DELETE /api/tax/users/{user_id}/income/{income_id}` - Delete income source
- `POST /api/tax/users/{user_id}/expenses/` - Add expense
- `GET /api/tax/users/{user_id}/expenses/` - Get user expenses
- `DELETE /api/tax/users/{user_id}/expenses/{expense_id}` - Delete expense
- `GET /api/tax/users/{user_id}/tax-calculation/` - Calculate tax liability
- `GET /api/tax/users/{user_id}/provisional-tax/` - Calculate provisional tax
- `POST /api/tax/users/{user_id}/custom-tax-calculation/` - Custom tax scenarios

### Administrative
- `POST /api/admin/update-tax-data` - Update tax data from SARS (Admin only)

### Health & Status
- `GET /` - Root endpoint with app information
- `GET /api/health` - Health check with database status

## Database Models

### Core Models
- **UserProfile**: User accounts with authentication and tax preferences
- **IncomeSource**: Multiple income streams per user
- **UserExpense**: Tax-deductible expenses with categorization
- **DeductibleExpenseType**: Predefined expense categories with limits

### Tax Data Models
- **TaxBracket**: Progressive tax brackets by year
- **TaxRebate**: Age-based tax rebates (primary, secondary, tertiary)
- **TaxThreshold**: Tax-free thresholds by age group
- **MedicalTaxCredit**: Medical scheme fee tax credits
- **TaxCalculation**: Stored tax calculation results

## Database Management

### Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Check migration status
alembic current
alembic history
```

### Administrative Tools
```bash
# Create admin user
python create_admin.py admin@example.com password123 Admin User

# List all users
python list_users.py

# Debug user profile
python debug_user_profile.py <user_id>

# Update tax data manually
python fetch_tax_data.py --year 2024-2025 --force
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_api/test_tax_calculator.py

# Run tests with verbose output
pytest -v
```

## Deployment

The application is configured for deployment on Render.com with the following structure:

- **Backend**: Web service with PostgreSQL database
- **Frontend**: Static site deployment
- **Environment**: Production configuration with appropriate CORS settings

See [DEPLOYMENT.md](./docs/DEPLOYMENT.md) for detailed deployment instructions.

## Documentation

For more detailed information, refer to:

- [Installation Guide](./docs/INSTALLATION.md): Complete setup instructions
- [Deployment Guide](./docs/DEPLOYMENT.md): Production deployment
- [API Documentation](./docs/API.md): Detailed API reference

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.