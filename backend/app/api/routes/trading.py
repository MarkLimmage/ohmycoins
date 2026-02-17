# mypy: ignore-errors
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, desc, select

from app.api.deps import CurrentUser, get_db
from app.models import (
    Order,
    OrderPublic,
    OrderRequest,
    OrderResponse,
    Position,
    PositionPublic,
)
from app.services.trading.executor import get_order_queue

router = APIRouter()

@router.post("/orders", response_model=OrderResponse)
async def place_order(
    session: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
    order_in: OrderRequest,
):
    """
    Place a new trading order.
    """
    # Create order in DB (pending)
    # OrderRequest inherits from OrderCreate which has basic fields
    # We need to explicitly set user_id

    # Note: OrderRequest is exactly OrderCreate.
    # Order has additional fields like status.

    order = Order(
        user_id=user.id,
        status="pending",
        **order_in.model_dump()
    )
    session.add(order)
    session.commit()
    session.refresh(order)

    # Submit to queue
    try:
        await get_order_queue().submit(order.id)
    except Exception as e:
        # Update order status to failed if submission fails
        order.status = "failed"
        order.error_message = f"Submission error: {str(e)}"
        session.add(order)
        session.commit()
        raise HTTPException(status_code=500, detail=f"Failed to submit order: {str(e)}")

    return order

@router.get("/orders", response_model=list[OrderPublic])
def read_orders(
    session: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve orders.
    """
    statement = select(Order).where(Order.user_id == user.id).order_by(desc(Order.created_at)).offset(skip).limit(limit)
    orders = session.exec(statement).all()
    return orders

@router.delete("/orders/{order_id}", response_model=OrderPublic)
def cancel_order(
    session: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
    order_id: UUID,
):
    """
    Cancel an order.
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if order.status in ['filled', 'cancelled', 'failed']:
        raise HTTPException(status_code=400, detail=f"Order already {order.status}")

    # TODO: If status is 'submitted', we should technically call the exchange to cancel.
    # However, for this sprint we handle internal queue cancellation.

    order.status = 'cancelled'
    session.add(order)
    session.commit()
    session.refresh(order)
    return order

@router.get("/positions", response_model=list[PositionPublic])
def read_positions(
    session: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
):
    """
    Retrieve positions.
    """
    statement = select(Position).where(Position.user_id == user.id)
    positions = session.exec(statement).all()
    return positions
