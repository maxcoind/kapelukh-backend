# API Documentation

## Base Information

- **Base URL**: `http://localhost:8000` (default)
- **API Version**: v1
- **Content-Type**: `application/json`
- **Authentication**: Bearer Token (JWT)

## Authentication

All protected endpoints require authentication via Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Token Expiration
- **Access Token**: 30 minutes
- **Refresh Token**: 24 hours (1440 minutes)

---

## Endpoints

### Authentication Endpoints

#### POST `/api/v1/auth/login`
Login with username and password using form data.

**Request:**
```
Content-Type: application/x-www-form-urlencoded

username=admin
password=admin
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Incorrect username or password"
}
```

---

#### POST `/api/v1/auth/refresh`
Refresh an expired access token using a valid refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Invalid refresh token"
}
```

---

#### GET `/api/v1/auth/me`
Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "username": "admin"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Could not validate credentials"
}
```

---

### Payment Endpoints

All payment endpoints require authentication.

#### POST `/api/v1/payments/`
Create a new payment.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
  "amount": 100.50,
  "date": "2026-01-13T12:00:00Z"
}
```

**Validation Rules:**
- `amount`: Decimal with 2 decimal places, max 10 digits, must be greater than 0
- `date`: ISO 8601 datetime string

**Response (201 Created):**
```json
{
  "id": 1,
  "amount": 100.50,
  "date": "2026-01-13T12:00:00Z"
}
```

**Error Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "loc": ["body", "amount"],
      "msg": "Input should be greater than 0",
      "type": "greater_than"
    }
  ]
}
```

---

#### GET `/api/v1/payments/{payment_id}`
Get a specific payment by ID.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `payment_id` (integer): Payment ID

**Response (200 OK):**
```json
{
  "id": 1,
  "amount": 100.50,
  "date": "2026-01-13T12:00:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Payment not found"
}
```

---

#### GET `/api/v1/payments/`
List all payments with pagination, filtering, and sorting support.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum number of records to return (default: 100)
- `customer_id` (integer, optional): Filter by customer ID
- `date_from` (datetime, optional): Filter payments after this date (ISO 8601 format)
- `date_to` (datetime, optional): Filter payments before this date (ISO 8601 format)
- `sort_by` (string, optional): Field to sort by. Valid values: `customer_id`, `amount`, `date`
- `sort_order` (string, optional): Sort order. Valid values: `asc`, `desc` (default: `asc`)

**Example - Pagination:** `/api/v1/payments/?skip=0&limit=10`

**Example - Sort by amount descending:** `/api/v1/payments/?sort_by=amount&sort_order=desc`

**Example - Filter and sort:** `/api/v1/payments/?customer_id=123&sort_by=date&sort_order=desc`

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "amount": 100.50,
    "date": "2026-01-13T12:00:00Z"
  },
  {
    "id": 2,
    "amount": 250.00,
    "date": "2026-01-13T14:30:00Z"
  }
]
```

---

#### PUT `/api/v1/payments/{payment_id}`
Update an existing payment.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `payment_id` (integer): Payment ID

**Request:**
```json
{
  "amount": 150.75,
  "date": "2026-01-13T15:00:00Z"
}
```

**Note:** All fields are optional. Only provided fields will be updated.

**Response (200 OK):**
```json
{
  "id": 1,
  "amount": 150.75,
  "date": "2026-01-13T15:00:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Payment not found"
}
```

---

#### DELETE `/api/v1/payments/{payment_id}`
Delete a payment by ID.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `payment_id` (integer): Payment ID

**Response (204 No Content)**
No content returned on successful deletion.

**Error Response (404 Not Found):**
```json
{
  "detail": "Payment not found"
}
```

---

### Health Check

#### GET `/health`
Check application and database health status.

**No authentication required.**

**Response (200 OK):**
```json
{
  "status": "ok",
  "database": "connected"
}
```

**Response (200 OK with database error):**
```json
{
  "status": "error",
  "database": "disconnected"
}
```

---

## Data Models

### PaymentCreate
```typescript
{
  amount: number;      // Decimal, 2 decimal places, > 0
  date: string;        // ISO 8601 datetime
}
```

### PaymentUpdate
```typescript
{
  amount?: number;     // Decimal, 2 decimal places, > 0
  date?: string;       // ISO 8601 datetime
}
```

### PaymentRead
```typescript
{
  id: number;
  amount: number;
  date: string;
}
```

### Token
```typescript
{
  access_token: string;
  refresh_token: string;
  token_type: string;
}
```

### RefreshTokenRequest
```typescript
{
  refresh_token: string;
}
```

### UserResponse
```typescript
{
  username: string;
}
```

---

## Common HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful deletion) |
| 400 | Bad Request |
| 401 | Unauthorized (invalid/missing token) |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

---

## Example cURL Commands

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

### Get Current User
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <your_access_token>"
```

### Create Payment
```bash
curl -X POST "http://localhost:8000/api/v1/payments/" \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100.50,
    "date": "2026-01-13T12:00:00Z"
  }'
```

### List Payments
```bash
curl -X GET "http://localhost:8000/api/v1/payments/?skip=0&limit=10" \
  -H "Authorization: Bearer <your_access_token>"
```

### List Payments Sorted by Amount (Descending)
```bash
curl -X GET "http://localhost:8000/api/v1/payments/?sort_by=amount&sort_order=desc" \
  -H "Authorization: Bearer <your_access_token>"
```

### List Payments Sorted by Date (Ascending) with Filters
```bash
curl -X GET "http://localhost:8000/api/v1/payments/?sort_by=date&sort_order=asc&customer_id=123" \
  -H "Authorization: Bearer <your_access_token>"
```

### Update Payment
```bash
curl -X PUT "http://localhost:8000/api/v1/payments/1" \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 150.75
  }'
```

### Delete Payment
```bash
curl -X DELETE "http://localhost:8000/api/v1/payments/{payment_id}" \
  -H "Authorization: Bearer <your_access_token>"
```

---

### Telegram Users Endpoints

All Telegram users endpoints require authentication.

#### POST `/api/v1/telegram-users/`
Create a new Telegram user.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
  "telegram_id": 123456789,
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "language_code": "en",
  "is_active": true,
  "is_bot": false
}
```

**Validation Rules:**
- `telegram_id`: Integer, must be greater than 0
- `username`: Optional, max 32 characters
- `first_name`: Required, max 64 characters
- `last_name`: Optional, max 64 characters
- `language_code`: Optional, max 10 characters
- `is_active`: Boolean (default: true)
- `is_bot`: Boolean (default: false)

**Response (201 Created):**
```json
{
  "id": 1,
  "telegram_id": 123456789,
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "language_code": "en",
  "is_active": true,
  "is_bot": false,
  "created_at": "2026-01-16T12:00:00Z",
  "updated_at": "2026-01-16T12:00:00Z",
  "last_interaction_at": null
}
```

**Error Response (409 Conflict):**
```json
{
  "detail": "Telegram user with ID 123456789 already exists"
}
```

---

#### GET `/api/v1/telegram-users/{telegram_id}`
Get a specific Telegram user by Telegram ID.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `telegram_id` (integer): Telegram user ID

**Response (200 OK):**
```json
{
  "id": 1,
  "telegram_id": 123456789,
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "language_code": "en",
  "is_active": true,
  "is_bot": false,
  "created_at": "2026-01-16T12:00:00Z",
  "updated_at": "2026-01-16T12:00:00Z",
  "last_interaction_at": "2026-01-16T14:30:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Telegram user not found"
}
```

---

#### GET `/api/v1/telegram-users/`
List Telegram users with pagination, filtering, and sorting support.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum number of records to return (default: 100, max: 1000)
- `telegram_id` (integer, optional): Filter by exact Telegram ID
- `username` (string, optional): Filter by username (contains, case-insensitive)
- `is_active` (boolean, optional): Filter by active status
- `is_bot` (boolean, optional): Filter by bot status
- `created_from` (datetime, optional): Filter users created after this date (ISO 8601 format)
- `created_to` (datetime, optional): Filter users created before this date (ISO 8601 format)
- `updated_from` (datetime, optional): Filter users updated after this date (ISO 8601 format)
- `updated_to` (datetime, optional): Filter users updated before this date (ISO 8601 format)
- `sort_by` (string, optional): Field to sort by. Valid values: `telegram_id`, `username`, `created_at`, `updated_at`, `last_interaction_at`
- `sort_order` (string, optional): Sort order. Valid values: `asc`, `desc` (default: `desc`)

**Example - Pagination:** `/api/v1/telegram-users/?skip=0&limit=10`

**Example - Filter by active status:** `/api/v1/telegram-users/?is_active=true`

**Example - Filter by username:** `/api/v1/telegram-users/?username=john`

**Example - Sort by creation date:** `/api/v1/telegram-users/?sort_by=created_at&sort_order=desc`

**Example - Filter and sort:** `/api/v1/telegram-users/?is_active=true&sort_by=created_at&sort_order=desc`

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "telegram_id": 123456789,
    "username": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "language_code": "en",
    "is_active": true,
    "is_bot": false,
    "created_at": "2026-01-16T12:00:00Z",
    "updated_at": "2026-01-16T12:00:00Z",
    "last_interaction_at": "2026-01-16T14:30:00Z"
  },
  {
    "id": 2,
    "telegram_id": 987654321,
    "username": "jane_smith",
    "first_name": "Jane",
    "last_name": "Smith",
    "language_code": "en",
    "is_active": true,
    "is_bot": false,
    "created_at": "2026-01-15T10:00:00Z",
    "updated_at": "2026-01-15T10:00:00Z",
    "last_interaction_at": null
  }
]
```

---

#### PUT `/api/v1/telegram-users/{telegram_id}`
Update an existing Telegram user.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `telegram_id` (integer): Telegram user ID

**Request:**
```json
{
  "first_name": "John Updated",
  "last_name": "Doe Updated",
  "is_active": false
}
```

**Note:** All fields are optional. Only provided fields will be updated. The `updated_at` field is automatically set to the current time.

**Response (200 OK):**
```json
{
  "id": 1,
  "telegram_id": 123456789,
  "username": "john_doe",
  "first_name": "John Updated",
  "last_name": "Doe Updated",
  "language_code": "en",
  "is_active": false,
  "is_bot": false,
  "created_at": "2026-01-16T12:00:00Z",
  "updated_at": "2026-01-16T12:30:00Z",
  "last_interaction_at": "2026-01-16T14:30:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Telegram user not found"
}
```

---

#### DELETE `/api/v1/telegram-users/{telegram_id}`
Soft delete a Telegram user (sets `is_active` to `false`).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `telegram_id` (integer): Telegram user ID

**Response (204 No Content)**
No content returned on successful deletion.

**Error Response (404 Not Found):**
```json
{
  "detail": "Telegram user not found"
}
```

**Note:** This is a soft delete - the user remains in the database but is marked as inactive (`is_active: false`).

---

#### PATCH `/api/v1/telegram-users/{telegram_id}/last-interaction`
Update the last interaction timestamp for a Telegram user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `telegram_id` (integer): Telegram user ID

**Request Body:** None

**Response (200 OK):**
```json
{
  "id": 1,
  "telegram_id": 123456789,
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "language_code": "en",
  "is_active": true,
  "is_bot": false,
  "created_at": "2026-01-16T12:00:00Z",
  "updated_at": "2026-01-16T12:30:00Z",
  "last_interaction_at": "2026-01-16T15:00:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Telegram user not found"
}
```

**Use Case:** Call this endpoint whenever a user interacts with your Telegram bot to track engagement.

---

### Telegram Users Data Models

#### TelegramUserCreate
```typescript
{
  telegram_id: number;      // Required, must be > 0
  username?: string;        // Optional, max 32 chars
  first_name: string;       // Required, max 64 chars
  last_name?: string;       // Optional, max 64 chars
  language_code?: string;   // Optional, max 10 chars
  is_active?: boolean;     // Optional, default: true
  is_bot?: boolean;        // Optional, default: false
}
```

#### TelegramUserUpdate
```typescript
{
  username?: string;        // Optional, max 32 chars
  first_name?: string;       // Optional, max 64 chars
  last_name?: string;       // Optional, max 64 chars
  language_code?: string;   // Optional, max 10 chars
  is_active?: boolean;     // Optional
  is_bot?: boolean;        // Optional
}
```

#### TelegramUserRead
```typescript
{
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string;
  last_name: string | null;
  language_code: string | null;
  is_active: boolean;
  is_bot: boolean;
  created_at: string;       // ISO 8601 datetime
  updated_at: string;       // ISO 8601 datetime
  last_interaction_at: string | null;  // ISO 8601 datetime or null
}
```

---

### Telegram Users Example cURL Commands

#### Create Telegram User
```bash
curl -X POST "http://localhost:8000/api/v1/telegram-users/" \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": 123456789,
    "username": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "language_code": "en"
  }'
```

#### Get Telegram User
```bash
curl -X GET "http://localhost:8000/api/v1/telegram-users/123456789" \
  -H "Authorization: Bearer <your_access_token>"
```

#### List Telegram Users (Active Only, Sorted by Created Date)
```bash
curl -X GET "http://localhost:8000/api/v1/telegram-users/?is_active=true&sort_by=created_at&sort_order=desc" \
  -H "Authorization: Bearer <your_access_token>"
```

#### List Telegram Users with Username Filter
```bash
curl -X GET "http://localhost:8000/api/v1/telegram-users/?username=john" \
  -H "Authorization: Bearer <your_access_token>"
```

#### Update Telegram User
```bash
curl -X PUT "http://localhost:8000/api/v1/telegram-users/123456789" \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John Updated"
  }'
```

#### Soft Delete Telegram User
```bash
curl -X DELETE "http://localhost:8000/api/v1/telegram-users/123456789" \
  -H "Authorization: Bearer <your_access_token>"
```

#### Update Last Interaction
```bash
curl -X PATCH "http://localhost:8000/api/v1/telegram-users/123456789/last-interaction" \
  -H "Authorization: Bearer <your_access_token>"
```

---

### Survey Endpoints

All survey endpoints require authentication.

#### POST `/api/v1/surveys/`
Create a new survey.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
  "user_id": 123456789,
  "full_name": {
    "first_name": "John",
    "last_name": "Doe"
  },
  "super_powers": ["coding", "leadership"],
  "birth_date": "1990-01-15",
  "traits_to_improve": ["patience", "public speaking"],
  "to_buy": ["laptop", "books"],
  "to_sell": ["old phone"],
  "service": "Consulting",
  "material_goal": "Buy a house",
  "social_goal": "Build a community",
  "spiritual_goal": "Find inner peace"
}
```

**Validation Rules:**
- `user_id`: Integer, must be greater than 0, unique
- `birth_date`: Required, non-empty string
- All other fields are optional and can be empty

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 123456789,
  "full_name": {
    "first_name": "John",
    "last_name": "Doe"
  },
  "super_powers": ["coding", "leadership"],
  "birth_date": "1990-01-15",
  "traits_to_improve": ["patience", "public speaking"],
  "to_buy": ["laptop", "books"],
  "to_sell": ["old phone"],
  "service": "Consulting",
  "material_goal": "Buy a house",
  "social_goal": "Build a community",
  "spiritual_goal": "Find inner peace",
  "created_at": "2026-01-19T12:00:00Z",
  "updated_at": "2026-01-19T12:00:00Z"
}
```

**Error Response (409 Conflict):**
```json
{
  "detail": "Survey for user with ID 123456789 already exists"
}
```

---

#### GET `/api/v1/surveys/{survey_id}`
Get a specific survey by ID.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `survey_id` (integer): Survey ID

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 123456789,
  "full_name": {
    "first_name": "John",
    "last_name": "Doe"
  },
  "super_powers": ["coding", "leadership"],
  "birth_date": "1990-01-15",
  "traits_to_improve": ["patience", "public speaking"],
  "to_buy": ["laptop", "books"],
  "to_sell": ["old phone"],
  "service": "Consulting",
  "material_goal": "Buy a house",
  "social_goal": "Build a community",
  "spiritual_goal": "Find inner peace",
  "created_at": "2026-01-19T12:00:00Z",
  "updated_at": "2026-01-19T12:00:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Survey not found"
}
```

---

#### GET `/api/v1/surveys/by-user/{user_id}`
Get a survey by user ID (Telegram ID).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `user_id` (integer): Telegram user ID

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 123456789,
  "full_name": {
    "first_name": "John",
    "last_name": "Doe"
  },
  "super_powers": ["coding", "leadership"],
  "birth_date": "1990-01-15",
  "traits_to_improve": ["patience", "public speaking"],
  "to_buy": ["laptop", "books"],
  "to_sell": ["old phone"],
  "service": "Consulting",
  "material_goal": "Buy a house",
  "social_goal": "Build a community",
  "spiritual_goal": "Find inner peace",
  "created_at": "2026-01-19T12:00:00Z",
  "updated_at": "2026-01-19T12:00:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Survey not found for this user"
}
```

---

#### GET `/api/v1/surveys/`
List surveys with pagination, filtering, and sorting support.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum number of records to return (default: 100)
- `user_id` (integer, optional): Filter by user ID
- `sort_by` (string, optional): Field to sort by. Valid values: `user_id`, `created_at`, `birth_date`
- `sort_order` (string, optional): Sort order. Valid values: `asc`, `desc` (default: `asc`)

**Example - Pagination:** `/api/v1/surveys/?skip=0&limit=10`

**Example - Filter by user ID:** `/api/v1/surveys/?user_id=123456789`

**Example - Sort by created date descending:** `/api/v1/surveys/?sort_by=created_at&sort_order=desc`

**Example - Filter and sort:** `/api/v1/surveys/?user_id=123456789&sort_by=created_at&sort_order=desc`

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user_id": 123456789,
    "full_name": {
      "first_name": "John",
      "last_name": "Doe"
    },
    "super_powers": ["coding", "leadership"],
    "birth_date": "1990-01-15",
    "traits_to_improve": ["patience", "public speaking"],
    "to_buy": ["laptop", "books"],
    "to_sell": ["old phone"],
    "service": "Consulting",
    "material_goal": "Buy a house",
    "social_goal": "Build a community",
    "spiritual_goal": "Find inner peace",
    "created_at": "2026-01-19T12:00:00Z",
    "updated_at": "2026-01-19T12:00:00Z"
  },
  {
    "id": 2,
    "user_id": 987654321,
    "full_name": {
      "first_name": "Jane",
      "last_name": "Smith"
    },
    "super_powers": ["design", "writing"],
    "birth_date": "1985-05-20",
    "traits_to_improve": ["time management"],
    "to_buy": [],
    "to_sell": [],
    "service": null,
    "material_goal": null,
    "social_goal": null,
    "spiritual_goal": null,
    "created_at": "2026-01-18T10:00:00Z",
    "updated_at": "2026-01-18T10:00:00Z"
  }
]
```

---

#### PUT `/api/v1/surveys/{survey_id}`
Update an existing survey.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `survey_id` (integer): Survey ID

**Request:**
```json
{
  "full_name": {
    "first_name": "John Updated",
    "last_name": "Doe"
  },
  "super_powers": ["coding", "leadership", "mentoring"],
  "service": "Premium Consulting",
  "material_goal": "Buy a house and a car"
}
```

**Note:** All fields are optional. Only provided fields will be updated. The `updated_at` field is automatically set to the current time.

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 123456789,
  "full_name": {
    "first_name": "John Updated",
    "last_name": "Doe"
  },
  "super_powers": ["coding", "leadership", "mentoring"],
  "birth_date": "1990-01-15",
  "traits_to_improve": ["patience", "public speaking"],
  "to_buy": ["laptop", "books"],
  "to_sell": ["old phone"],
  "service": "Premium Consulting",
  "material_goal": "Buy a house and a car",
  "social_goal": "Build a community",
  "spiritual_goal": "Find inner peace",
  "created_at": "2026-01-19T12:00:00Z",
  "updated_at": "2026-01-19T12:30:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Survey not found"
}
```

---

#### DELETE `/api/v1/surveys/{survey_id}`
Delete a survey by ID.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `survey_id` (integer): Survey ID

**Response (204 No Content)**
No content returned on successful deletion.

**Error Response (404 Not Found):**
```json
{
  "detail": "Survey not found"
}
```

---

### Survey Data Models

#### SurveyCreate
```typescript
{
  user_id: number;                           // Required, must be > 0, unique
  full_name?: Record<string, string>;        // Optional, e.g., {first_name: "John", last_name: "Doe"}
  super_powers?: string[];                   // Optional, array of super powers
  birth_date: string;                        // Required, non-empty string
  traits_to_improve?: string[];             // Optional, array of traits
  to_buy?: string[];                         // Optional, array of items to buy
  to_sell?: string[];                        // Optional, array of items to sell
  service?: string | null;                   // Optional, service description
  material_goal?: string | null;            // Optional, material goal
  social_goal?: string | null;              // Optional, social goal
  spiritual_goal?: string | null;           // Optional, spiritual goal
}
```

#### SurveyUpdate
```typescript
{
  full_name?: Record<string, string>;        // Optional
  super_powers?: string[];                   // Optional
  birth_date?: string;                       // Optional
  traits_to_improve?: string[];             // Optional
  to_buy?: string[];                         // Optional
  to_sell?: string[];                        // Optional
  service?: string | null;                   // Optional
  material_goal?: string | null;            // Optional
  social_goal?: string | null;              // Optional
  spiritual_goal?: string | null;           // Optional
}
```

#### SurveyRead
```typescript
{
  id: number;
  user_id: number;
  full_name: Record<string, string>;
  super_powers: string[];
  birth_date: string;
  traits_to_improve: string[];
  to_buy: string[];
  to_sell: string[];
  service: string | null;
  material_goal: string | null;
  social_goal: string | null;
  spiritual_goal: string | null;
  created_at: string;                        // ISO 8601 datetime
  updated_at: string;                        // ISO 8601 datetime
}
```

---

### Survey Example cURL Commands

#### Create Survey
```bash
curl -X POST "http://localhost:8000/api/v1/surveys/" \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123456789,
    "full_name": {
      "first_name": "John",
      "last_name": "Doe"
    },
    "super_powers": ["coding", "leadership"],
    "birth_date": "1990-01-15",
    "traits_to_improve": ["patience", "public speaking"],
    "to_buy": ["laptop", "books"],
    "to_sell": ["old phone"],
    "service": "Consulting",
    "material_goal": "Buy a house",
    "social_goal": "Build a community",
    "spiritual_goal": "Find inner peace"
  }'
```

#### Get Survey by ID
```bash
curl -X GET "http://localhost:8000/api/v1/surveys/1" \
  -H "Authorization: Bearer <your_access_token>"
```

#### Get Survey by User ID
```bash
curl -X GET "http://localhost:8000/api/v1/surveys/by-user/123456789" \
  -H "Authorization: Bearer <your_access_token>"
```

#### List Surveys (Sorted by Created Date Descending)
```bash
curl -X GET "http://localhost:8000/api/v1/surveys/?sort_by=created_at&sort_order=desc" \
  -H "Authorization: Bearer <your_access_token>"
```

#### List Surveys Filtered by User ID
```bash
curl -X GET "http://localhost:8000/api/v1/surveys/?user_id=123456789" \
  -H "Authorization: Bearer <your_access_token>"
```

#### Update Survey
```bash
curl -X PUT "http://localhost:8000/api/v1/surveys/1" \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": {
      "first_name": "John Updated",
      "last_name": "Doe"
    },
    "service": "Premium Consulting"
  }'
```

#### Delete Survey
```bash
curl -X DELETE "http://localhost:8000/api/v1/surveys/1" \
  -H "Authorization: Bearer <your_access_token>"
```

---

## Interactive API Documentation

The API includes interactive Swagger UI documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Environment Configuration

Default credentials (can be configured via `.env` file):
- **Username**: `admin`
- **Password**: `admin`

See `.env.example` for all available configuration options.
