from typing import List, Optional, Literal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks

from app.auth import get_current_user
from app.crud import payment as payment_crud
from app.crud.payment import SortField, SortOrder
from app.database import getDbSession
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate
from app.websocket.routes import get_connection_manager
from app.websocket.integration import ModelEventHelper
from app.websocket.plugins.payment_plugin import PaymentPlugin

router = APIRouter()


async def trigger_payment_event(
    payment: Payment, event_type: Literal["created", "updated", "deleted"], session
):
    """Trigger payment event via EventProcessor."""
    connection_manager = get_connection_manager()

    plugin = PaymentPlugin()
    await ModelEventHelper.trigger_event(
        db=session,
        connection_manager=connection_manager,
        topic="payment",
        event_type=event_type,
        instance=payment,
        to_dict_func=plugin.to_dict,
    )


@router.post("/", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def create_payment(
    *,
    session=Depends(getDbSession),
    payment_in: PaymentCreate,
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks,
) -> Payment:
    payment = await payment_crud.create(session=session, payment_create=payment_in)
    background_tasks.add_task(trigger_payment_event, payment, "created", session)
    return payment


@router.get("/{payment_id}", response_model=PaymentRead)
async def read_payment(
    *,
    session=Depends(getDbSession),
    payment_id: int,
    current_user: str = Depends(get_current_user),
) -> Payment:
    payment = await payment_crud.get(session=session, payment_id=payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )
    return payment


@router.get("/", response_model=List[PaymentRead])
async def read_payments(
    *,
    session=Depends(getDbSession),
    skip: int = 0,
    limit: int = 100,
    customer_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort_by: Optional[SortField] = Query(
        None, description="Field to sort by (customer_id, amount, date)"
    ),
    sort_order: Optional[SortOrder] = Query(
        SortOrder.asc, description="Sort order (asc, desc)"
    ),
    current_user: str = Depends(get_current_user),
) -> List[Payment]:
    payments = await payment_crud.get_multi(
        session=session,
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return payments


@router.put("/{payment_id}", response_model=PaymentRead)
async def update_payment(
    *,
    session=Depends(getDbSession),
    payment_id: int,
    payment_in: PaymentUpdate,
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks,
) -> Payment:
    db_payment = await payment_crud.get(session=session, payment_id=payment_id)
    if not db_payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )
    payment = await payment_crud.update(
        session=session, db_obj=db_payment, obj_in=payment_in
    )
    background_tasks.add_task(trigger_payment_event, payment, "updated", session)
    return payment


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    *,
    session=Depends(getDbSession),
    payment_id: int,
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks,
) -> None:
    payment = await payment_crud.remove(session=session, payment_id=payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )
    background_tasks.add_task(trigger_payment_event, payment, "deleted", session)
