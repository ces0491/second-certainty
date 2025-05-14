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
cp .env.example .env
```

Edit the `.env` file with your configuration:

```
# Database connection
DATABASE_URL=postgresql://user:password@localhost:5432/second_certainty
# For SQLite: DATABASE_URL=sqlite:///./app.db

# Authentication
SECRET_KEY=your_secure_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 1 week

# SARS website configuration
SARS_WEBSITE_URL=https://www.sars.gov.za

# Application settings
DEBUG=True
ENVIRONMENT=development  # development, staging, production
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

For a secure `SECRET_KEY`, you can generate one with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Set Up the Database

#### Using SQLite (Simple Setup)

If you're using SQLite, the database will be created automatically when you run:

```bash
python init_db.py
```

#### Using PostgreSQL

If you're using PostgreSQL:

1. Create a PostgreSQL database:

```bash
psql -U postgres
CREATE DATABASE second_certainty;
CREATE USER second_certainty_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE second_certainty TO second_certainty_user;
\q
```

2. Update the `DATABASE_URL` in your `.env` file.

3. Initialize the database:

```bash
python init_db.py
```

### 6. Seed the Database

Populate the database with initial data:

```bash
python scripts/seed_data.py
```

### 7. Setup Admin Account

To create an admin account:

```bash
python add_admin_field.py your_email@example.com
```

### 8. Start the Backend Server

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000.

## Frontend Setup

### 1. Clone the Frontend Repository

If the frontend is in a separate repository:

```bash
git clone https://github.com/ces0491/second-certainty-frontend.git
cd second-certainty-frontend
```

If the frontend is included in the main repository, navigate to the frontend directory.

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

1. Terminal 1 (Backend):
```bash
cd /path/to/second-certainty
source venv/bin/activate # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload
```

2. Terminal 2 (Frontend):
```bash
cd /path/to/second-certainty-frontend
npm start
```

## Testing

### Backend Tests

To run the backend tests:

```bash
pytest
```

For test coverage:

```bash
pytest --cov=app tests/
```

### Frontend Tests

To run the frontend tests:

```bash
npm test
```

## Database Migrations

We use Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Troubleshooting

### Common Issues

#### Backend

- **Database Connection Error**: Verify your database credentials in the `.env` file.
- **Import Errors**: Ensure you've activated your virtual environment.
- **Port Already in Use**: Change the port in the Uvicorn command: `uvicorn app.main:app --reload --port 8001`

#### Frontend

- **API Connection Error**: Check that the backend server is running and that the `REACT_APP_API_BASE_URL` is correct.
- **Node Module Errors**: Try deleting `node_modules` folder and running `npm install` again.
- **Port Already in Use**: You can select a different port: `PORT=3001 npm start`

## Next Steps

After installation:

1. Create a user account via the registration page
2. Log in to the application
3. Add income sources and expenses
4. Explore the tax calculation features

For more information on using the application, refer to the [User Guide](./docs/user-guide.qmd).