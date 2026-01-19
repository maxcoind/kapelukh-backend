# How to Add a New Model

This guide explains how to add a new model to the system based on the Payments model pattern.

## Overview

Adding a new model requires creating 5 files and updating 3 existing files:

1. **Model** (`app/models/{model_name}.py`) - Database schema
2. **Schemas** (`app/schemas/{model_name}.py`) - Pydantic models for API
3. **CRUD** (`app/crud/{model_name}.py`) - Database operations
4. **API Router** (`app/api/{model_name}.py`) - REST endpoints
5. **WebSocket Plugin** (`app/websocket/plugins/{model_name}_plugin.py`) - Real-time subscriptions
6. **API Module** - Update `app/api/__init__.py`
7. **Main App** - Update `app/main.py`
8. **Plugin Registry** - Update `app/websocket/plugins/__init__.py`

## Step 1: Create the Model

File: `app/models/{model_name}.py`

```python
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


class {ModelName}(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # Add your fields here
    name: str = Field(max_length=64, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Key Points:**
- Use `SQLModel` with `table=True`
- Primary key: `Optional[int] = Field(default=None, primary_key=True)`
- Index frequently queried fields: `index=True`
- Use `datetime.now(timezone.utc)` for timestamps
- Use `Field()` for constraints (max_length, gt, etc.)

## Step 2: Create Schemas

File: `app/schemas/{model_name}.py`

```python
from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SortField(str, Enum):
    # Add fields you want to sort by
    name = "name"
    created_at = "created_at"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class {ModelName}Base(BaseModel):
    # Common fields
    name: str


class {ModelName}Create({ModelName}Base):
    # Add validation for create
    name: str = Field(min_length=1, max_length=64)


class {ModelName}Update(BaseModel):
    # All Optional for partial updates
    name: Optional[str] = Field(None, min_length=1, max_length=64)


class {ModelName}Read({ModelName}Base):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

**Key Points:**
- `{ModelName}Base` - common fields
- `{ModelName}Create` - extends Base with validation
- `{ModelName}Update` - all Optional fields for partial updates
- `{ModelName}Read` - includes id and timestamps
- Add `SortField` and `SortOrder` enums for listing

## Step 3: Create CRUD Operations

File: `app/crud/{model_name}.py`

```python
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlmodel import and_, asc, desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.{model_name} import {ModelName}
from app.schemas.{model_name} import {ModelName}Create, {ModelName}Update


class SortField(str, Enum):
    # Same as in schemas
    name = "name"
    created_at = "created_at"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


async def create(*, session: AsyncSession, {model_name}_create: {ModelName}Create) -> {ModelName}:
    db_obj = {ModelName}.model_validate({model_name}_create)
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def get(*, session: AsyncSession, {model_name}_id: int) -> Optional[{ModelName}]:
    return await session.get({ModelName}, {model_name}_id)


async def get_multi(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    # Add optional filter parameters
    name: Optional[str] = None,
    sort_by: Optional[SortField] = None,
    sort_order: Optional[SortOrder] = None,
) -> List[{ModelName}]:
    statement = select({ModelName})
    conditions = []

    # Add filters
    if name is not None:
        conditions.append({ModelName}.name.contains(name))

    if conditions:
        statement = statement.where(and_(*conditions))

    # Add sorting
    if sort_by:
        sort_column = getattr({ModelName}, sort_by.value)
        if sort_order == SortOrder.desc:
            statement = statement.order_by(desc(sort_column))
        else:
            statement = statement.order_by(asc(sort_column))

    statement = statement.offset(skip).limit(limit)
    result = await session.exec(statement)
    return list(result.all())


async def update(
    *, session: AsyncSession, db_obj: {ModelName}, obj_in: {ModelName}Update
) -> {ModelName}:
    obj_data = obj_in.model_dump(exclude_unset=True)
    for field, value in obj_data.items():
        setattr(db_obj, field, value)
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def remove(*, session: AsyncSession, {model_name}_id: int) -> Optional[{ModelName}]:
    obj = await session.get({ModelName}, {model_name}_id)
    if obj:
        await session.delete(obj)
        await session.commit()
    return obj
```

**Key Points:**
- Use `select()` for queries
- Use `and_()` for multiple conditions
- Use `getattr()` for dynamic column sorting
- Use `model_dump(exclude_unset=True)` for partial updates
- Return None if not found in `remove()`

## Step 4: Create API Router

File: `app/api/{model_name}.py`

```python
from typing import List, Optional, Literal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks

from app.auth import get_current_user
from app.crud import {model_name} as {model_name}_crud
from app.crud.{model_name} import SortField, SortOrder
from app.database import getDbSession
from app.models.{model_name} import {ModelName}
from app.schemas.{model_name} import {ModelName}Create, {ModelName}Read, {ModelName}Update
from app.websocket.routes import get_connection_manager
from app.websocket.integration import ModelEventHelper
from app.websocket.plugins.{model_name}_plugin import {ModelName}Plugin

router = APIRouter()


async def trigger_{model_name}_event(
    {model_name}: {ModelName}, event_type: Literal["created", "updated", "deleted"], session
):
    """Trigger {model_name} event via EventProcessor."""
    connection_manager = get_connection_manager()

    plugin = {ModelName}Plugin()
    await ModelEventHelper.trigger_event(
        db=session,
        connection_manager=connection_manager,
        topic="{model_name}",
        event_type=event_type,
        instance={model_name},
        to_dict_func=plugin.to_dict,
    )


@router.post("/", response_model={ModelName}Read, status_code=status.HTTP_201_CREATED)
async def create_{model_name}(
    *,
    session=Depends(getDbSession),
    {model_name}_in: {ModelName}Create,
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks,
) -> {ModelName}:
    {model_name} = await {model_name}_crud.create(session=session, {model_name}_create={model_name}_in)
    background_tasks.add_task(trigger_{model_name}_event, {model_name}, "created", session)
    return {model_name}


@router.get("/{{{model_name}_id}}", response_model={ModelName}Read)
async def read_{model_name}(
    *,
    session=Depends(getDbSession),
    {model_name}_id: int,
    current_user: str = Depends(get_current_user),
) -> {ModelName}:
    {model_name} = await {model_name}_crud.get(session=session, {model_name}_id={model_name}_id)
    if not {model_name}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="{ModelName} not found"
        )
    return {model_name}


@router.get("/", response_model=List[{ModelName}Read])
async def read_{model_name}s(
    *,
    session=Depends(getDbSession),
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = Query(None),
    sort_by: Optional[SortField] = Query(
        None, description="Field to sort by"
    ),
    sort_order: Optional[SortOrder] = Query(
        SortOrder.asc, description="Sort order (asc, desc)"
    ),
    current_user: str = Depends(get_current_user),
) -> List[{ModelName}]:
    {model_name}s = await {model_name}_crud.get_multi(
        session=session,
        skip=skip,
        limit=limit,
        name=name,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return {model_name}s


@router.put("/{{{model_name}_id}}", response_model={ModelName}Read)
async def update_{model_name}(
    *,
    session=Depends(getDbSession),
    {model_name}_id: int,
    {model_name}_in: {ModelName}Update,
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks,
) -> {ModelName}:
    db_{model_name} = await {model_name}_crud.get(session=session, {model_name}_id={model_name}_id)
    if not db_{model_name}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="{ModelName} not found"
        )
    {model_name} = await {model_name}_crud.update(
        session=session, db_obj=db_{model_name}, obj_in={model_name}_in
    )
    background_tasks.add_task(trigger_{model_name}_event, {model_name}, "updated", session)
    return {model_name}


@router.delete("/{{{model_name}_id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{model_name}(
    *,
    session=Depends(getDbSession),
    {model_name}_id: int,
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks,
) -> None:
    {model_name} = await {model_name}_crud.remove(session=session, {model_name}_id={model_name}_id)
    if not {model_name}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="{ModelName} not found"
        )
    background_tasks.add_task(trigger_{model_name}_event, {model_name}, "deleted", session)
```

**Key Points:**
- Use `BackgroundTasks` for non-blocking WebSocket events
- Use `Depends(get_current_user)` for auth
- Use `Depends(getDbSession)` for database
- Return 404 for not found
- Use proper HTTP status codes
- Background events: "created", "updated", "deleted"

## Step 5: Create WebSocket Plugin

File: `app/websocket/plugins/{model_name}_plugin.py`

```python
from typing import Type
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.{model_name} import {ModelName}
from app.websocket.plugin_system import ModelPlugin
from app.schemas.websocket import SubscriptionParams


class {ModelName}Plugin(ModelPlugin):
    """Plugin for {ModelName} model."""

    topic: str = "{model_name}"
    model_class: Type[SQLModel] = {ModelName}
    primary_key: str = "id"

    async def to_dict(self, instance: {ModelName}) -> dict:
        """Convert {model_name} instance to dictionary."""
        return {
            "id": instance.id,
            "name": instance.name,
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
        }

    async def fetch_initial_data(
        self, session: AsyncSession, params: SubscriptionParams
    ) -> dict:
        """Fetch initial {model_name}s for subscription."""
        query = select({ModelName}).order_by({ModelName}.created_at.desc()).limit(100)
        result = await session.execute(query)
        {model_name}s = result.scalars().all()

        return {
            "items": [await self.to_dict(m) for m in {model_name}s],
            "total": len({model_name}s),
        }
```

**Key Points:**
- Implement `topic`, `model_class`, `primary_key`
- `to_dict()` - convert model to JSON-serializable dict
- `fetch_initial_data()` - return `{"items": [...], "total": n}`

## Step 6: Update API Module

File: `app/api/__init__.py`

```python
from app.api.auth import router as auth_router
from app.api.payments import router as payments_router
from app.api.{model_name} import router as {model_name}_router  # Add this

__all__ = ["auth_router", "payments_router", "{model_name}_router"]  # Add this
```

## Step 7: Update Main App

File: `app/main.py`

```python
# Add import
from .api import payments_router, {model_name}_router

# In lifespan() - plugins are auto-registered

# Add router
app.include_router({model_name}_router, prefix="/api/v1/{model_name}s", tags=["{model_name}s"])
```

## Step 8: Update Plugin Registry

File: `app/websocket/plugins/__init__.py`

```python
from app.websocket.plugin_system import ModelRegistry, model_registry, ModelPlugin
from app.websocket.plugins.payment_plugin import PaymentPlugin
from app.websocket.plugins.{model_name}_plugin import {ModelName}Plugin  # Add this


def register_plugins():
    """Register all model plugins."""
    registry = model_registry

    # Register plugins
    registry.register(PaymentPlugin())
    registry.register({ModelName}Plugin())  # Add this


__all__ = [
    "ModelPlugin",
    "ModelRegistry",
    "model_registry",
    "PaymentPlugin",
    "{ModelName}Plugin",  # Add this
    "register_plugins",
]
```

## Step 9: Create Tests (Optional but Recommended)

File: `tests/test_{model_name}.py`

```python
import pytest
from httpx import AsyncClient

from app.models.{model_name} import {ModelName}


@pytest.mark.asyncio
async def test_create_{model_name}(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/{model_name}s/",
        json={"name": "Test Name"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Name"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_{model_name}(client: AsyncClient, auth_headers: dict, db_session):
    obj = {ModelName}(name="Test Name")
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)

    response = await client.get(
        f"/api/v1/{model_name}s/{obj.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Name"


@pytest.mark.asyncio
async def test_get_{model_name}s(client: AsyncClient, auth_headers: dict, db_session):
    for i in range(3):
        obj = {ModelName}(name=f"Name {i}")
        db_session.add(obj)
    await db_session.commit()

    response = await client.get(
        "/api/v1/{model_name}s/",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_update_{model_name}(client: AsyncClient, auth_headers: dict, db_session):
    obj = {ModelName}(name="Original Name")
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)

    response = await client.put(
        f"/api/v1/{model_name}s/{obj.id}",
        json={"name": "Updated Name"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_{model_name}(client: AsyncClient, auth_headers: dict, db_session):
    obj = {ModelName}(name="Test Name")
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)

    response = await client.delete(
        f"/api/v1/{model_name}s/{obj.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204
```

## Verification Steps

After creating all files:

1. **Run linter**:
   ```bash
   ruff check .
   ```

2. **Run tests**:
   ```bash
   pytest tests/test_{model_name}.py
   ```

3. **Run all tests**:
   ```bash
   pytest
   ```

4. **Start server**:
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Test API**:
   - GET `/health` - check server is running
   - GET `/api/v1/{model_name}s/` - list items
   - POST `/api/v1/{model_name}s/` - create item
   - GET `/api/v1/{model_name}s/{id}` - get single item
   - PUT `/api/v1/{model_name}s/{id}` - update item
   - DELETE `/api/v1/{model_name}s/{id}` - delete item

## Naming Convention Examples

| Entity | Model Class | File Name | Router Prefix |
|--------|-------------|-----------|---------------|
| Payment | Payment | payment.py | /api/v1/payments |
| User | User | user.py | /api/v1/users |
| Order | Order | order.py | /api/v1/orders |
| TelegramUser | TelegramUser | telegram_user.py | /api/v1/telegram-users |

## Common Patterns

### Soft Delete (instead of hard delete):
```python
# Model
is_active: bool = Field(default=True)

# CRUD update (in remove)
async def remove(*, session: AsyncSession, {model_name}_id: int) -> Optional[{ModelName}]:
    obj = await session.get({ModelName}, {model_name}_id)
    if obj:
        obj.is_active = False
        session.add(obj)
        await session.commit()
    return obj
```

### Relationships:
```python
# Model
class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    order_id: int = Field(index=True)
```

### Unique Constraints:
```python
# Model
class User(SQLModel, table=True):
    email: str = Field(index=True, unique=True)
```

### Default Values:
```python
# Model
status: str = Field(default="pending")
```

## File Structure Summary

```
app/
├── models/
│   └── {model_name}.py          (1)
├── schemas/
│   └── {model_name}.py          (2)
├── crud/
│   └── {model_name}.py          (3)
├── api/
│   ├── __init__.py              (4) - update
│   └── {model_name}.py          (5)
├── websocket/
│   ├── plugins/
│   │   ├── __init__.py          (6) - update
│   │   └── {model_name}_plugin.py (7)
└── main.py                      (8) - update
```
