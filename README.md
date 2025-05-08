# Second Certainty Tax API

A comprehensive South African tax liability management API that helps users track, calculate, and optimize their tax obligations throughout the fiscal year.

## Overview

The Second Certainty Tax Tool addresses one of life's two certainties—taxes—by providing individuals and small businesses with an intuitive platform for managing tax liabilities throughout the fiscal year. Traditional tax management often occurs reactively at year-end, leading to unexpected liabilities, missed deductions, and financial stress.

Our application transforms this approach by implementing a proactive, year-round tax management system that continuously calculates estimated tax liabilities based on income streams, identifies potential deductions, forecasts quarterly payments, and provides optimization strategies—all in real-time.

## Features

- **User Authentication**: Secure JWT-based authentication system
- **Profile Management**: Create and manage user tax profiles
- **Income Tracking**: Log multiple income sources (salary, freelance, investments, etc.)
- **Expense Management**: Record and categorize tax-deductible expenses
- **Real-time Tax Liability**: Calculate current tax position at any time
- **Tax Data**: Up-to-date tax brackets, rebates, thresholds
- **SARS Integration**: Automatic scraping of latest tax rates from SARS website
- **Provisional Tax**: Calculate and track provisional tax payments
- **Data Validation**: Comprehensive input validation and error handling

## Technology Stack

- **Framework**: FastAPI 0.110.1
- **ORM**: SQLAlchemy 2.0.40
- **Validation**: Pydantic 2.6.0
- **Database**: PostgreSQL (or SQLite for development)
- **Authentication**: JWT with password hashing
- **Testing**: Pytest 7.4.4
- **Documentation**: OpenAPI (Swagger UI)
- **HTTP Client**: HTTPX 0.27.0
- **Server**: Uvicorn 0.29.0

## Project Structure

```
second-certainty/
│
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   └── tax_calculator.py   # Tax calculation endpoints
│   │   ├── __init__.py
│   │   └── dependencies.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auth.py                 # Authentication logic
│   │   ├── config.py               # Configuration settings
│   │   ├── data_scraper.py         # SARS website scraper
│   │   ├── exceptions.py           # Custom exceptions
│   │   └── tax_calculator.py       # Tax calculation engine
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── session.py
│   │   └── migrations/             # Alembic migrations
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── tax_models.py           # SQLAlchemy models
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── tax_schemas.py          # Pydantic schemas
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   └── tax_utils.py            # Utility functions
│   │
│   ├── __init__.py
│   └── main.py                     # Application entry point
│
├── docs/                           # Documentation
│
├── scripts/
│   ├── seed_data.py                # Database seeding
│   └── update_tax_tables.py        # Manual tax data update
│
├── tests/
│   ├── test_api/
│   ├── test_core/
│   ├── test_utils/
│   ├── __init__.py
│   └── conftest.py
│
├── .env.example                    # Environment variables template
├── Dockerfile                      # Docker configuration
├── docker-compose.yml              # Docker Compose configuration
├── requirements.txt                # Python dependencies
├── setup.py                        # Package setup
└── README.md                       # Project documentation
```

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL (optional, SQLite can be used for development)
- Git

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/ces0491/second-certainty.git
   cd second-certainty
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a .env file from the example:
   ```bash
   cp .env.example .env
   ```
   Edit the .env file with your configuration.

5. Initialize the database:
   ```bash
   python scripts/seed_data.py
   ```

6. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/ces0491/second-certainty.git
   cd second-certainty
   ```

2. Create a .env file from the example:
   ```bash
   cp .env.example .env
   ```
   Edit the .env file with your configuration.

3. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

The API will be available at http://localhost:8000.

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/token` - Get JWT access token
- `GET /api/auth/me` - Get current user info

### Tax Calculation

- `GET /api/tax/tax-brackets/` - Get tax brackets for a specific tax year
- `GET /api/tax/deductible-expenses/` - Get all deductible expense types
- `POST /api/tax/users/{user_id}/income/` - Add income source for a user
- `GET /api/tax/users/{user_id}/income/` - Get all income sources for a user
- `DELETE /api/tax/users/{user_id}/income/{income_id}` - Delete an income source
- `POST /api/tax/users/{user_id}/expenses/` - Add expense for a user
- `GET /api/tax/users/{user_id}/expenses/` - Get all expenses for a user
- `DELETE /api/tax/users/{user_id}/expenses/{expense_id}` - Delete an expense
- `GET /api/tax/users/{user_id}/tax-calculation/` - Calculate tax liability
- `GET /api/tax/users/{user_id}/provisional-tax/` - Calculate provisional tax
- `POST /api/tax/update-tax-data/` - Update tax data from SARS website

## Documentation

API documentation is available at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Testing

Run the tests with pytest:

```bash
pytest
```

For test coverage:

```bash
pytest --cov=app tests/
```

## Development

### Adding New Routes

1. Create a new file in `app/api/routes/`
2. Define endpoints using FastAPI router
3. Include the router in `app/main.py`

### Database Migrations

We use Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Deployment

### Production Configuration

For production deployment:

1. Set a secure `SECRET_KEY` in the .env file
2. Configure a production-ready database
3. Set up TLS/SSL for HTTPS
4. Enable rate limiting
5. Set up monitoring and logging

### Deployment Options

- **Docker**: Use the provided Dockerfile and docker-compose.yml
- **Kubernetes**: Deploy using Kubernetes manifests (not included)
- **AWS**: Deploy on AWS ECS or EKS
- **Heroku**: Deploy directly from GitHub

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- South African Revenue Service (SARS) for providing tax information
- The FastAPI team for the API framework

---

## Roadmap

Future improvements planned for the Second Certainty Tax API:

- Integration with banking APIs for automatic income and expense tracking
- Tax optimization recommendations
- Multi-year tax planning tools
- Mobile app integration
- Data visualization for tax trends
- Support for business entities (PTY, CC)
- Integration with popular accounting software