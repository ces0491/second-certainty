# API Documentation

This document provides detailed information about the Second Certainty Tax API endpoints and usage.

## Base URL

- **Development**: `http://localhost:8000/api`
- **Production**: `https://second-certainty-api.onrender.com/api`

## Interactive Documentation

For interactive API documentation:

- **Swagger UI**: `https://second-certainty-api.onrender.com/api/docs`
- **ReDoc**: `https://second-certainty-api.onrender.com/api/redoc`

## Authentication

The API uses JWT (JSON Web Token) for authentication with HTTPBearer security scheme.

### Register a User

```http

POST /api/auth/register

```text

**Request Body:**

```json

{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "John",
  "surname": "Doe",
  "date_of_birth": "1980-01-01",
  "is_provisional_taxpayer": false
}

```text

**Response (201 Created):**

```json

{
  "message": "User created successfully",
  "user_id": 1
}

```text

### Login (JSON)

```http

POST /api/auth/login

```text

**Request Body:**

```json

{
  "email": "user@example.com",
  "password": "secure_password"
}

```text

**Response (200 OK):**

```json

{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John",
    "surname": "Doe",
    "is_provisional_taxpayer": false,
    "is_admin": false
  }
}

```text

### Login (OAuth2 Compatible)

```http

POST /api/auth/token

```text

**Request Body (Form Data):**

- `username`: User's email
- `password`: User's password

**Response (200 OK):**

```json

{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}

```text

### Get Current User

```http

GET /api/auth/me

```text

**Headers:**

```text
Authorization: Bearer {access_token}

```text

**Response (200 OK):**

```json

{
  "id": 1,
  "email": "user@example.com",
  "name": "John",
  "surname": "Doe",
  "date_of_birth": "1980-01-01",
  "is_provisional_taxpayer": false,
  "is_admin": false,
  "created_at": "2025-01-01"
}

```text

### Update Profile

```http

PUT /api/auth/profile

```text

**Request Body (all fields optional):**

```json

{
  "name": "John",
  "surname": "Smith",
  "date_of_birth": "1980-01-01",
  "is_provisional_taxpayer": true
}

```text

### Change Password

```http

PUT /api/auth/change-password

```text

**Request Body:**

```json

{
  "current_password": "old_password",
  "new_password": "new_secure_password"
}

```text

### Logout

```http

POST /api/auth/logout

```text

**Response (200 OK):**

```json

{
  "message": "Successfully logged out"
}

```text

## Tax Calculation Endpoints

### Get Tax Brackets

```http

GET /api/tax/tax-brackets/

```text

**Query Parameters:**

- `tax_year` (optional): Tax year in format "YYYY-YYYY" (default: current tax year)

**Response (200 OK):**

```json

[
  {
    "lower_limit": 1,
    "upper_limit": 237100,
    "rate": 0.18,
    "base_amount": 0,
    "tax_year": "2024-2025"
  },
  {
    "lower_limit": 237101,
    "upper_limit": 370500,
    "rate": 0.26,
    "base_amount": 42678,
    "tax_year": "2024-2025"
  }
]

```text

### Get Deductible Expense Types

```http

GET /api/tax/deductible-expenses/

```text

**Response (200 OK):**

```json

[
  {
    "id": 1,
    "name": "Retirement Annuity Contributions",
    "description": "Contributions to retirement annuities",
    "max_deduction": 350000,
    "max_percentage": 27.5,
    "is_active": true
  }
]

```text

### Add Income Source

```http

POST /api/tax/users/{user_id}/income/

```text

**Request Body:**

```json

{
  "source_type": "Salary",
  "description": "Main employment",
  "annual_amount": 600000,
  "is_paye": true,
  "tax_year": "2024-2025"
}

```text

**Response (201 Created):**

```json

{
  "id": 1,
  "user_id": 1,
  "source_type": "Salary",
  "description": "Main employment",
  "annual_amount": 600000,
  "is_paye": true,
  "tax_year": "2024-2025",
  "created_at": "2025-05-14",
  "updated_at": "2025-05-14"
}

```text

### Get Income Sources

```http

GET /api/tax/users/{user_id}/income/

```text

**Query Parameters:**

- `tax_year` (optional): Tax year in format "YYYY-YYYY"

**Response (200 OK):**

```json

[
  {
    "id": 1,
    "user_id": 1,
    "source_type": "Salary",
    "description": "Main employment",
    "annual_amount": 600000,
    "is_paye": true,
    "tax_year": "2024-2025",
    "created_at": "2025-05-14",
    "updated_at": "2025-05-14"
  }
]

```text

### Delete Income Source

```http

DELETE /api/tax/users/{user_id}/income/{income_id}

```text

**Response (204 No Content)**

### Add Expense

```http

POST /api/tax/users/{user_id}/expenses/

```text

**Request Body:**

```json

{
  "expense_type_id": 1,
  "description": "Monthly RA contribution",
  "amount": 24000,
  "tax_year": "2024-2025"
}

```text

**Response (201 Created):**

```json

{
  "id": 1,
  "user_id": 1,
  "expense_type_id": 1,
  "description": "Monthly RA contribution",
  "amount": 24000,
  "tax_year": "2024-2025",
  "created_at": "2025-05-14",
  "expense_type": {
    "id": 1,
    "name": "Retirement Annuity Contributions",
    "description": "Contributions to retirement annuities",
    "max_deduction": 350000,
    "max_percentage": 27.5,
    "is_active": true
  }
}

```text

### Get Expenses

```http

GET /api/tax/users/{user_id}/expenses/

```text

**Query Parameters:**

- `tax_year` (optional): Tax year in format "YYYY-YYYY"

**Response (200 OK):**

```json

[
  {
    "id": 1,
    "user_id": 1,
    "expense_type_id": 1,
    "expense_type": {
      "id": 1,
      "name": "Retirement Annuity Contributions",
      "description": "Contributions to retirement annuities",
      "max_deduction": 350000,
      "max_percentage": 27.5,
      "is_active": true
    },
    "description": "Monthly RA contribution",
    "amount": 24000,
    "tax_year": "2024-2025",
    "created_at": "2025-05-14"
  }
]

```text

### Delete Expense

```http

DELETE /api/tax/users/{user_id}/expenses/{expense_id}

```text

**Response (204 No Content)**

### Calculate Tax Liability

```http

GET /api/tax/users/{user_id}/tax-calculation/

```text

**Query Parameters:**

- `tax_year` (optional): Tax year in format "YYYY-YYYY"

**Response (200 OK):**

```json

{
  "gross_income": 600000,
  "taxable_income": 576000,
  "tax_before_rebates": 176030,
  "rebates": 17235,
  "medical_credits": 347,
  "final_tax": 154631,
  "effective_tax_rate": 0.2686,
  "monthly_tax_rate": 0.0215
}

```text

### Calculate Custom Tax Scenario

```http

POST /api/tax/users/{user_id}/custom-tax-calculation/

```text

**Request Body:**

```json

{
  "income": 600000,
  "age": 35,
  "expenses": {
    "retirement_annuity": 24000,
    "medical_expenses": 5000
  }
}

```text

**Query Parameters:**

- `tax_year` (optional): Tax year in format "YYYY-YYYY"

**Response (200 OK):**

```json

{
  "gross_income": 600000,
  "taxable_income": 571000,
  "tax_before_rebates": 174930,
  "rebates": 17235,
  "medical_credits": 347,
  "final_tax": 153561,
  "effective_tax_rate": 0.2689,
  "monthly_tax_rate": 0.0213
}

```text

### Calculate Provisional Tax

```http

GET /api/tax/users/{user_id}/provisional-tax/

```text

**Query Parameters:**

- `tax_year` (optional): Tax year in format "YYYY-YYYY"

**Response (200 OK):**

```json

{
  "total_tax": 154631,
  "taxable_income": 576000,
  "effective_tax_rate": 0.2686,
  "first_payment": {
    "amount": 77315.5,
    "due_date": "2025-08-31"
  },
  "second_payment": {
    "amount": 77315.5,
    "due_date": "2026-02-28"
  }
}

```text

## Administrative Endpoints

### Update Tax Data (Admin Only)

```http

POST /api/admin/update-tax-data

```text

**Query Parameters:**

- `force` (optional): Override existing data (default: false)
- `year` (optional): Tax year to update (default: current)

**Headers:**

```text
Authorization: Bearer {admin_access_token}

```text

**Response (200 OK):**

```json

{
  "message": "Tax data update initiated",
  "force": false,
  "year": "2024-2025"
}

```text

## Health Check Endpoints

### Root Endpoint

```http

GET /

```text

**Response (200 OK):**

```json

{
  "app_name": "Second Certainty",
  "version": "1.0.0",
  "message": "Welcome to the Second Certainty Tax API"
}

```text

### Health Check

```http

GET /api/health

```text

**Response (200 OK):**

```json

{
  "status": "healthy",
  "timestamp": "2025-06-18T12:34:56.789Z",
  "version": "1.0.0",
  "database": {
    "status": "healthy",
    "error": null
  },
  "environment": {
    "status": "healthy",
    "missing": null
  }
}

```text

## Error Responses

The API returns standard HTTP status codes:

- **400 Bad Request**: Invalid request body or parameters
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: Authenticated user doesn't have permission
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation errors
- **500 Internal Server Error**: Server-side error

### Error Response Format

```json

{
  "detail": "Error message describing what went wrong"
}

```text

### Validation Error Response

```json

{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}

```text

## Authentication

All protected endpoints require a valid JWT token in the Authorization header:

```text
Authorization: Bearer {access_token}

```text

Tokens expire after 7 days (10080 minutes) by default.

## Rate Limiting

The API implements rate limiting:

- 100 requests per minute for general endpoints
- 5 requests per minute for authentication endpoints

Exceeding these limits will result in a 429 Too Many Requests response.

## Tax Year Format

Tax years are represented in the format "YYYY-YYYY" (e.g., "2024-2025").
The South African tax year runs from March 1 to February 28/29 of the following year.

## User Authorization

Users can only access their own data. Attempting to access another user's data will result in a 403 Forbidden response, unless the user has admin privileges.

## CORS Support

The API supports Cross-Origin Resource Sharing (CORS) for:

- Development: `http://localhost:3000`
- Production: `https://second-certainty.onrender.com`

## OpenAPI Schema

The complete OpenAPI schema is available at:

- Development: `http://localhost:8000/api/openapi.json`
- Production: `https://second-certainty-api.onrender.com/api/openapi.json`
