# AGENTS.md

This file contains guidelines for agents working on this FastAPI backend codebase.

## Build/Test/Lint Commands

```bash
# Run all tests
pytest

# Run a single test
pytest tests/test_telegram_users.py::test_create_telegram_user

# Run tests with coverage
pytest --cov=app

# Run linting
ruff check .

# Run linting with auto-fix
ruff check . --fix

# Format code
ruff format .

# Start development server
uvicorn app.main:app --reload

# Start with specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Code Style Guidelines

### Import Organization
- Standard library imports first
- Third-party imports second
- Local app imports third
- Group imports with blank lines between groups
- Use `from typing import` for type hints

Example:
```python
from typing import Optional, List
from datetime import datetime

from fastapi import Depends, HTTPException
from sqlalchemy import select

from app.auth import get_current_user
from app.models.user import User
```

### Naming Conventions
- **Classes**: PascalCase (TelegramUser, PaymentService)
- **Functions/Methods**: snake_case (create_user, get_payment)
- **Variables**: snake_case (user_id, payment_amount)
- **Private functions**: _prefix (_validate_input, _calculate_total)
- **Constants**: UPPER_SNAKE_CASE (MAX_RETRIES, DEFAULT_TIMEOUT)
- **Models**: {Entity}Name (TelegramUser, Payment)
- **Schemas**: {Entity}Base, {Entity}Create, {Entity}Update, {Entity}Read
- **CRUD functions**: {action}_{entity} (create_user, get_user, update_user)

### Type Hints
- Always specify return types on functions
- Use `Optional[Type]` for nullable fields (Python <3.10) or `Type | None`
- Use `List[Type]` for collections
- Use `Literal` for enumerated string values
- Use `Dict[str, Any]` for flexible dictionaries
- Import `Any` from typing module

Example:
```python
async def create_user(
    db: AsyncSession,
    user_data: UserCreate,
) -> Optional[User]:
    pass
```

### Async/Await
- All database operations use async/await
- API route handlers are async
- Use `async def` for all I/O operations
- Use `await` for database queries, HTTP requests

### Database/Models
- Use SQLModel for database models
- Inherit from SQLModel with `table=True`
- Use `Field()` for constraints and defaults
- **Datetime fields**: Use `Column(DateTime(timezone=True), nullable=False)` with `default_factory=lambda: datetime.now(timezone.utc)`
- **Optional datetime fields**: Use `Column(DateTime(timezone=True))` with `default=None`
- Soft delete: use `is_active` boolean field instead of hard deletes
- Query with SQLAlchemy's `select()` and async session

Example:
```python
from sqlmodel import Column, DateTime, Field, SQLModel
from datetime import datetime, timezone

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=64)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    last_seen: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True)),
        default=None,
    )
```

### API Routes
- Use `APIRouter` for route organization
- Prefix routes with `/api/v1/{resource}`
- Use proper HTTP status codes from `fastapi.status`
- Return Pydantic models as `response_model`
- Use `Depends()` for dependencies (auth, db session)
- Raise `HTTPException` for errors

Example:
```python
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create(
    *,
    session: AsyncSession = Depends(getDbSession),
    user_data: UserCreate,
    current_user: str = Depends(get_current_user),
) -> User:
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data"
        )
    return await create_user(session, user_data)
```

### Error Handling
- Use `HTTPException` for API errors with appropriate status codes
- Log errors with `logger.error()` including exception details
- Use 400 for client errors, 401 for auth, 404 for not found, 409 for conflicts
- Return JSON with `detail` key for error messages

### Schemas (Pydantic)
- Base schema with common fields
- Create schema extends Base (with validation)
- Update schema has all Optional fields
- Read schema includes id and timestamps
- Use `Field()` for validation rules

Example:
```python
class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

class UserRead(UserBase):
    id: int
    created_at: datetime
```

### Testing
- All tests use `@pytest.mark.asyncio` decorator
- Test functions start with `test_`
- Use descriptive names: `test_create_user_success`, `test_get_user_not_found`
- Use fixtures for db session, client, auth headers
- Import test dependencies from `app.main`
- Test both success and failure cases
- Use `async_client: AsyncClient` for API tests

Example:
```python
@pytest.mark.asyncio
async def test_create_user(async_client: AsyncClient, auth_headers: dict):
    response = await async_client.post(
        "/api/v1/users/",
        json={"name": "Test User"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test User"
```

### Logging
- Get logger with `logger = get_logger(__name__)`
- Use appropriate log levels: debug, info, warning, error
- Include context in log messages
- Log important operations (startup, shutdown, errors)
- Avoid logging sensitive data (passwords, tokens)

### Background Tasks
- Use `BackgroundTasks` for non-blocking operations
- Add tasks with `background_tasks.add_task(func, *args)`
- Use for event notifications, cleanup operations

### Docstrings
- Use triple quotes `"""` for docstrings
- Keep them concise and descriptive
- Document complex functions and classes
- Include parameter and return types for public functions

Example:
```python
async def create_user(
    db: AsyncSession,
    user_data: UserCreate,
) -> User:
    """Create a new user in the database.
    
    Args:
        db: Async database session
        user_data: User creation data
        
    Returns:
        Created user instance
    """
    pass
```

### Configuration
- Use `pydantic-settings` for configuration
- Access settings via `settings` singleton
- Use `SecretStr` for sensitive values
- Environment variables defined in `.env.example`

### WebSocket
- Use WebSocket for real-time updates
- Register plugins for model change notifications
- Use connection manager for client management
- Events triggered on CRUD operations

### Project Structure
- `app/api/` - API route handlers
- `app/models/` - SQLModel database models
- `app/schemas/` - Pydantic schemas
- `app/crud/` - Database operations
- `app/services/` - Business logic, external services
- `app/auth.py` - Authentication utilities
- `app/config.py` - Configuration management
- `app/database.py` - Database connection
- `app/logger.py` - Logging configuration
- `tests/` - Test files
- `docs/` - Documentation

### Best Practices
- Always use async/await for database and I/O operations
- Validate input with Pydantic models
- Handle errors gracefully and return proper HTTP status codes
- Use dependency injection for db sessions and auth
- Keep route handlers thin, delegate to CRUD/services
- Write tests for new features and bug fixes
- Run linter before committing changes
- Keep functions focused and single-purpose
- Use type hints throughout for better IDE support
