from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.db import get_db
from app.models.inventory import InventoryPosition
from app.models.events import InventoryEvent
from app.schemas.inventory import PositionCreate, EventCreate

router = APIRouter()


@router.get("/v1/inventory/availability")
async def get_availability(
    item_id: UUID,
    path_ids: str = Query(..., description="Comma-separated path IDs"),
    seller_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get available inventory for an item across specified paths."""
    path_id_list = [int(p.strip()) for p in path_ids.split(",")]

    query = select(InventoryPosition).where(
        and_(
            InventoryPosition.item_id == item_id,
            InventoryPosition.path_id.in_(path_id_list),
            InventoryPosition.node_enabled == True,  # noqa: E712
        )
    )
    if seller_id:
        query = query.where(InventoryPosition.seller_id == seller_id)

    result = await db.execute(query)
    positions = result.scalars().all()

    # Group by path_id
    path_groups: dict[int, list[dict]] = defaultdict(list)
    for pos in positions:
        sellable = pos.available_qty - pos.reserved_qty
        path_groups[pos.path_id].append(
            {
                "fulfillment_node": pos.fulfillment_node,
                "available_qty": pos.available_qty,
                "reserved_qty": pos.reserved_qty,
                "sellable_qty": max(0, sellable),
                "node_enabled": pos.node_enabled,
            }
        )

    paths = []
    for pid in path_id_list:
        nodes = path_groups.get(pid, [])
        total_sellable = sum(n["sellable_qty"] for n in nodes)
        paths.append(
            {
                "path_id": pid,
                "path_code": "",  # caller maps path_id to path_code
                "total_sellable": total_sellable,
                "nodes": nodes,
            }
        )

    return {
        "item_id": str(item_id),
        "seller_id": str(seller_id) if seller_id else None,
        "paths": paths,
    }


@router.post("/v1/inventory/positions", status_code=201)
async def create_position(
    payload: PositionCreate, db: AsyncSession = Depends(get_db)
):
    """Admin/seed endpoint to create inventory positions."""
    pos = InventoryPosition(
        item_id=payload.item_id,
        fulfillment_node=payload.fulfillment_node,
        path_id=payload.path_id,
        seller_id=payload.seller_id,
        available_qty=payload.available_qty,
        reserved_qty=payload.reserved_qty,
        node_enabled=payload.node_enabled,
    )
    db.add(pos)
    await db.commit()
    return {"status": "created"}


@router.post("/v1/inventory/events", status_code=201)
async def create_event(
    payload: EventCreate, request: Request, db: AsyncSession = Depends(get_db)
):
    """Submit an inventory event. Updates position and publishes to Redis Stream."""
    new_qty = None

    # Atomic update: single SQL statement avoids read-modify-write race condition
    if payload.delta is not None and payload.seller_id and payload.path_id:
        stmt = (
            update(InventoryPosition)
            .where(
                and_(
                    InventoryPosition.item_id == payload.item_id,
                    InventoryPosition.fulfillment_node == payload.fulfillment_node,
                    InventoryPosition.path_id == payload.path_id,
                    InventoryPosition.seller_id == payload.seller_id,
                )
            )
            .values(
                available_qty=func.greatest(
                    0, InventoryPosition.available_qty + payload.delta
                )
            )
            .returning(InventoryPosition.available_qty)
        )
        result = await db.execute(stmt)
        row = result.first()
        new_qty = row[0] if row else None

    # Record the event
    event = InventoryEvent(
        event_type=payload.event_type,
        item_id=payload.item_id,
        fulfillment_node=payload.fulfillment_node,
        path_id=payload.path_id,
        seller_id=payload.seller_id,
        delta=payload.delta,
        new_available_qty=new_qty,
    )
    db.add(event)
    await db.commit()

    # Publish to Redis Stream
    publisher = request.app.state.stream_publisher
    if publisher and new_qty is not None:
        event_type = "stock_depleted" if new_qty <= 0 else "stock_updated"
        await publisher.publish(event_type, {
            "item_id": str(payload.item_id),
            "fulfillment_node": payload.fulfillment_node,
            "path_id": payload.path_id,
            "seller_id": str(payload.seller_id) if payload.seller_id else None,
            "delta": payload.delta,
            "new_available_qty": new_qty,
        })

    return {"status": "recorded", "new_available_qty": new_qty}
