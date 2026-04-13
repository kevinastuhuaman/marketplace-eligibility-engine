from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import and_, case, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.db import get_db
from app.models.events import InventoryEvent
from app.models.inventory import FulfillmentNode, InventoryPosition
from app.schemas.inventory import EventCreate, FulfillmentNodeCreate, PositionCreate
from app.services.confidence_service import score_inventory_position, summarize_path_confidence
from app.services.node_routing_service import build_alternative_nodes

router = APIRouter()
PACIFIC = ZoneInfo("America/Los_Angeles")


@router.get("/v1/inventory/availability")
async def get_availability(
    item_id: UUID,
    path_ids: str = Query(..., description="Comma-separated path IDs"),
    seller_id: UUID | None = None,
    primary_node: str | None = None,
    nearby_nodes: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get available inventory for an item across specified paths."""
    path_id_list = [int(part.strip()) for part in path_ids.split(",")]
    nearby_node_ids = [node.strip() for node in nearby_nodes.split(",") if node.strip()] if nearby_nodes else []

    query = select(InventoryPosition).where(
        and_(
            InventoryPosition.item_id == item_id,
            InventoryPosition.path_id.in_(path_id_list),
            InventoryPosition.node_enabled.is_(True),
        )
    )
    if seller_id:
        query = query.where(InventoryPosition.seller_id == seller_id)

    result = await db.execute(query)
    positions = result.scalars().all()

    node_ids = {
        position.fulfillment_node
        for position in positions
        if position.fulfillment_node
    }.union({primary_node} if primary_node else set()).union(set(nearby_node_ids))

    nodes_by_id: dict[str, FulfillmentNode] = {}
    if node_ids:
        node_result = await db.execute(
            select(FulfillmentNode).where(FulfillmentNode.node_id.in_(list(node_ids)))
        )
        nodes_by_id = {node.node_id: node for node in node_result.scalars().all()}

    path_groups: dict[int, list[InventoryPosition]] = defaultdict(list)
    for position in positions:
        path_groups[position.path_id].append(position)

    paths = []
    for path_id in path_id_list:
        positions_for_path = path_groups.get(path_id, [])
        scoped_positions = [position for position in positions_for_path if position.node_enabled]
        primary_positions = (
            [position for position in scoped_positions if position.fulfillment_node == primary_node]
            if primary_node
            else scoped_positions
        )
        visible_positions = primary_positions if primary_node else scoped_positions
        total_sellable = sum(
            max(int(position.available_qty or 0) - int(position.reserved_qty or 0), 0)
            for position in visible_positions
        )
        confidence = summarize_path_confidence(scoped_positions, primary_node=primary_node)
        alternative_nodes = build_alternative_nodes(
            scoped_positions,
            nodes_by_id,
            primary_node=primary_node,
            nearby_nodes=nearby_node_ids,
        )

        nodes = []
        for position in visible_positions:
            node_confidence = score_inventory_position(position)
            node_record = nodes_by_id.get(position.fulfillment_node)
            nodes.append(
                {
                    "fulfillment_node": position.fulfillment_node,
                    "node_name": node_record.node_name if node_record else position.fulfillment_node,
                    "available_qty": int(position.available_qty or 0),
                    "reserved_qty": int(position.reserved_qty or 0),
                    "sellable_qty": max(int(position.available_qty or 0) - int(position.reserved_qty or 0), 0),
                    "node_enabled": position.node_enabled,
                    "confidence_score": node_confidence["confidence_score"],
                    "confidence_band": node_confidence["confidence_band"],
                    "confidence_reason": node_confidence["confidence_reason"],
                    "last_verified_at": (
                        node_confidence["last_verified_at"].isoformat()
                        if node_confidence["last_verified_at"]
                        else None
                    ),
                    "node_type": position.node_type,
                }
            )
        paths.append(
            {
                "path_id": path_id,
                "path_code": "",
                "total_sellable": total_sellable,
                "confidence_score": confidence["confidence_score"],
                "confidence_band": confidence["confidence_band"],
                "confidence_reason": confidence["confidence_reason"],
                "last_verified_at": (
                    confidence["last_verified_at"].isoformat()
                    if confidence["last_verified_at"]
                    else None
                ),
                "alternative_nodes": alternative_nodes,
                "nodes": nodes,
            }
        )

    return {
        "item_id": str(item_id),
        "seller_id": str(seller_id) if seller_id else None,
        "paths": paths,
    }


@router.post("/v1/inventory/positions", status_code=201)
async def create_position(payload: PositionCreate, db: AsyncSession = Depends(get_db)):
    position = InventoryPosition(
        item_id=payload.item_id,
        fulfillment_node=payload.fulfillment_node,
        path_id=payload.path_id,
        seller_id=payload.seller_id,
        available_qty=payload.available_qty,
        reserved_qty=payload.reserved_qty,
        node_enabled=payload.node_enabled,
        confidence_score=payload.confidence_score,
        **({"last_verified_at": payload.last_verified_at} if payload.last_verified_at is not None else {}),
        verification_source=payload.verification_source,
        oos_30d_count=payload.oos_30d_count,
        node_type=payload.node_type,
    )
    db.add(position)
    await db.commit()
    return {"status": "created"}


@router.get("/v1/inventory/nodes")
async def list_nodes(
    market_code: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(FulfillmentNode).order_by(FulfillmentNode.node_name)
    if market_code:
        query = query.where(FulfillmentNode.market_code == market_code)

    result = await db.execute(query)
    nodes = result.scalars().all()
    return [
        {
            "node_id": node.node_id,
            "market_code": node.market_code,
            "node_name": node.node_name,
            "node_type": node.node_type,
            "latitude": float(node.latitude),
            "longitude": float(node.longitude),
            "enabled": node.enabled,
            "metadata": node.metadata_ or {},
        }
        for node in nodes
    ]


@router.post("/v1/inventory/nodes", status_code=201)
async def create_node(payload: FulfillmentNodeCreate, db: AsyncSession = Depends(get_db)):
    node = FulfillmentNode(
        node_id=payload.node_id,
        market_code=payload.market_code,
        node_name=payload.node_name,
        node_type=payload.node_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        enabled=payload.enabled,
        metadata_=payload.metadata or {},
    )
    db.add(node)
    await db.commit()
    return {"node_id": node.node_id}


@router.post("/v1/inventory/events", status_code=201)
async def create_event(
    payload: EventCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    new_qty = None

    if payload.delta is not None and payload.seller_id and payload.path_id:
        new_qty_expr = func.greatest(0, InventoryPosition.available_qty + payload.delta)
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
                available_qty=new_qty_expr,
                last_verified_at=datetime.now(PACIFIC),
                verification_source="inventory_event",
                oos_30d_count=case(
                    (
                        and_(
                            InventoryPosition.available_qty > 0,
                            new_qty_expr <= 0,
                        ),
                        InventoryPosition.oos_30d_count + 1,
                    ),
                    else_=InventoryPosition.oos_30d_count,
                ),
            )
            .returning(InventoryPosition.available_qty)
        )
        result = await db.execute(stmt)
        row = result.first()
        new_qty = row[0] if row else None

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

    publisher = getattr(request.app.state, "stream_publisher", None)
    if publisher and new_qty is not None:
        await publisher.publish(
            "stock_updated" if new_qty > 0 else "stock_depleted",
            {
                "item_id": str(payload.item_id),
                "fulfillment_node": payload.fulfillment_node,
                "path_id": payload.path_id,
                "seller_id": str(payload.seller_id) if payload.seller_id else None,
                "delta": payload.delta,
                "new_available_qty": new_qty,
            },
        )

    return {"status": "recorded", "new_available_qty": new_qty}
