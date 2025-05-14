# API Documentation

This document provides detailed information about the Second Certainty Tax API endpoints and usage.

## Base URL

- **Development**: `http://localhost:8000/api`
- **Production**: `https://second-certainty-api.onrender.com/api`

## Interactive Documentation

For interactive API documentation:

- **Swagger UI**: `{base_url}/docs`
- **ReDoc**: `{base_url}/redoc`

## Authentication

The API uses JWT (JSON Web Token) for authentication.

### Register a User

```
POST /auth/register
```

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
```

**Response (201 Created):**

```json
{
  "message": "User created successfully"
}
```

### Get Access Token

```
POST /auth/token
```

**Request Body:**

Form data with:
- `username`: User's email
- `password`: User's password

**Response (200 OK):**

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Authentication Header

For all protected endpoints, include the token in the Authorization header:

```
Authorization: Bearer {access_token}
```

## Tax Calculation Endpoints

### Get Tax Brackets

```
GET /tax/tax-brackets/
```

Query Parameters:
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
  },
  ...
]
```

### Get Deductible Expense Types

```
GET /tax/deductible-expenses/
```

**Response (200 OK):**

```json
[
  {
    "id": 1,
    "name": "Retirement Annuity Contributions",
    "description": "Contributions to retirement annuities",
    "max_deduction": 350000,
    "max_percentage": 27.5
  },
  ...
]
```

### Add Income Source

```
POST /tax/users/{user_id}/income/
```

**Request Body:**

```json
{
  "source_type": "Salary",
  "description": "Main employment",
  "annual_amount": 600000,
  "is_paye": true,
  "tax_year": "2024-2025"
}
```

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
  "created_at": "2025-05-14"
}
```

### Get Income Sources

```
GET /tax/users/{user_id}/income/
```

Query Parameters:
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
    "created_at": "2025-05-14"
  },
  ...
]
```

### Delete Income Source

```
DELETE /tax/users/{user_id}/income/{income_id}
```

**Response (204 No Content)**

### Add Expense

```
POST /tax/users/{user_id}/expenses/
```

**Request Body:**

```json
{
  "expense_type_id": 1,
  "description": "Monthly contribution",
  "amount": 24000,
  "tax_year": "2024-2025"
}
```

**Response (201 Created):**

```json
{
  "id": 1,
  "user_id": 1,
  "expense_type_id": 1,
  "description": "Monthly contribution",
  "amount": 24000,
  "tax_year": "2024-2025",
  "created_at": "2025-05-14"
}
```

### Get Expenses

```
GET /tax/users/{user_id}/expenses/
```

Query Parameters:
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
      "max_percentage": 27.5
    },
    "description": "Monthly contribution",
    "amount": 24000,
    "tax_year": "2024-2025",
    "created_at": "2025-05-14"
  },
  ...
]
```

### Delete Expense

```
DELETE /tax/users/{user_id}/expenses/{expense_id}
```

**Response (204 No Content)**

### Calculate Tax Liability

```
GET /tax/users/{user_id}/tax-calculation/
```

Query Parameters:
- `tax_year` (optional): Tax year in format "YYYY-YYYY"

**Response (200 OK):**

```json
{
  "gross_income": 600000,
  "taxable_income": 576000,
  "tax_before_rebates": 176030,
  "rebates": 17235,
  "medical_credits": 4164,
  "final_tax": 154631,
  "effective_tax_rate": 0.2686,
  "monthly_tax_rate": 0.0243
}
```

### Calculate Provisional Tax

```
GET /tax/users/{user_id}/provisional-tax/
```

Query Parameters:
- `tax_year` (optional): Tax year in format "YYYY-YYYY"

**Response (200 OK):**

```json
{
  "annual_tax": 154631,
  "first_payment": 77315.5,
  "second_payment": 77315.5,
  "final_payment": 0
}
```

### Update Tax Data

```
POST /tax/update-tax-data/
```

**Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "tax_year": "2024-2025",
    "brackets": [...],
    "rebates": {...},
    "thresholds": {...},
    "medical_credits": {...}
  }
}
```

## Administrative Endpoints

### Update Tax Data (Admin Only)

```
POST /admin/update-tax-data
```

Query Parameters:
- `force` (optional): Override existing data (default: false)
- `year` (optional): Tax year to update (default: current)

**Response (200 OK):**

```json
{
  "message": "Tax data update initiated",
  "force": false,
  "year": "2024-2025"
}
```

## Error Responses

The API returns standard HTTP status codes:

- **400 Bad Request**: Invalid request body or parameters
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: Authenticated user doesn't have permission
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server-side error

Error response body:

```json
{
  "detail": "Error message"
}
```

## Data Models

### User Profile

```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John",
  "surname": "Doe",
  "date_of_birth": "1980-01-01",
  "is_provisional_taxpayer": false,
  "is_admin": false,
  "created_at": "2025-05-01",
  "updated_at": "2025-05-01"
}
```

### Income Source

```json
{
  "id": 1,
  "user_id": 1,
  "source_type": "Salary",
  "description": "Main employment",
  "annual_amount": 600000,
  "is_paye": true,
  "tax_year": "2024-2025",
  "created_at": "2025-05-01",
  "updated_at": "2025-05-01"
}
```

### Expense

```json
{
  "id": 1,
  "user_id": 1,
  "expense_type_id": 1,
  "expense_type": {
    "id": 1,
    "name": "Retirement Annuity Contributions",
    "description": "Contributions to retirement annuities",
    "max_deduction": 350000,
    "max_percentage": 27.5
  },
  "description": "Monthly contribution",
  "amount": 24000,
  "tax_year": "2024-2025",
  "created_at": "2025-05-01",
  "updated_at": "2025-05-01"
}
```

### Tax Bracket

```json
{
  "lower_limit": 1,
  "upper_limit": 237100,
  "rate": 0.18,
  "base_amount": 0,
  "tax_year": "2024-2025"
}
```

### Tax Rebate

```json
{
  "primary": 17235,
  "secondary": 9444,
  "tertiary": 3145,
  "tax_year": "2024-2025"
}
```

### Tax Threshold

```json
{
  "below_65": 95750,
  "age_65_to_74": 148217,
  "age_75_plus": 165689,
  "tax_year": "2024-2025"
}
```

### Medical Tax Credit

```json
{
  "main_member": 347,
  "additional_member": 347,
  "tax_year": "2024-2025"
}
```

## Rate Limiting

The API implements basic rate limiting to prevent abuse:

- 100 requests per minute per IP address
- 1000 requests per hour per IP address

Exceeding these limits will result in a 429 Too Many Requests response.

## Pagination

List endpoints support pagination via query parameters:

- `skip`: Number of items to skip
- `limit`: Maximum number of items to return

Example:

```
GET /tax/users/{user_id}/income/?skip=0&limit=10
```

## API Versioning

The current API version is v1, which is implied in the base URL. Future versions will be explicitly versioned:

```
/api/v2/...
```

## CORS Support

The API supports Cross-Origin Resource Sharing (CORS) for the following origins:

- Development: `http://localhost:3000`
- Production: `https://second-certainty.onrender.com`

## Client Implementation Examples

### JavaScript (Axios)

```javascript
// Get access token
const getToken = async () => {
  const response = await axios.post('https://second-certainty-api.onrender.com/api/auth/token', 
    new URLSearchParams({
      'username': 'user@example.com',
      'password': 'secure_password'
    }),
    {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    }
  );
  return response.data.access_token;
};

// Get tax calculation
const getTaxCalculation = async (userId, token) => {
  const response = await axios.get(
    `https://second-certainty-api.onrender.com/api/tax/users/${userId}/tax-calculation/`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  return response.data;
};
```

### Python (Requests)

```python
import requests

# Get access token
def get_token():
    response = requests.post(
        'https://second-certainty-api.onrender.com/api/auth/token',
        data={
            'username': 'user@example.com',
            'password': 'secure_password'
        }
    )
    return response.json()['access_token']

# Get tax calculation
def get_tax_calculation(user_id, token):
    response = requests.get(
        f'https://second-certainty-api.onrender.com/api/tax/users/{user_id}/tax-calculation/',
        headers={
            'Authorization': f'Bearer {token}'
        }
    )
    return response.json()
```