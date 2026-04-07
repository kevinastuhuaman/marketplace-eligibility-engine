from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.items import Item
from app.schemas.items import ItemCreate

router = APIRouter()


@router.get("/v1/items/{item_id}")
async def get_item(item_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item).where(Item.item_id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {
        "item_id": item.item_id,
        "sku": item.sku,
        "name": item.name,
        "item_type": item.item_type,
        "category_path": str(item.category_path) if item.category_path else None,
        "attributes": item.attributes or {},
        "compliance_tags": item.compliance_tags or [],
        "display_metadata": item.display_metadata or {},
        "created_at": item.created_at,
    }


@router.get("/v1/items")
async def list_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item).order_by(Item.created_at.desc()).limit(100))
    items = result.scalars().all()
    return [
        {
            "item_id": item.item_id,
            "sku": item.sku,
            "name": item.name,
            "item_type": item.item_type,
            "category_path": str(item.category_path) if item.category_path else None,
            "attributes": item.attributes or {},
            "compliance_tags": item.compliance_tags or [],
            "display_metadata": item.display_metadata or {},
            "created_at": item.created_at,
        }
        for item in items
    ]


@router.post("/v1/items", status_code=201)
async def create_item(payload: ItemCreate, db: AsyncSession = Depends(get_db)):
    from sqlalchemy_utils import Ltree

    item = Item(
        sku=payload.sku,
        name=payload.name,
        item_type=payload.item_type,
        category_path=Ltree(payload.category_path) if payload.category_path else None,
        attributes=payload.attributes or {},
        compliance_tags=payload.compliance_tags or [],
        display_metadata=payload.display_metadata,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {
        "item_id": item.item_id,
        "sku": item.sku,
        "name": item.name,
        "item_type": item.item_type,
        "category_path": str(item.category_path) if item.category_path else None,
        "attributes": item.attributes or {},
        "compliance_tags": item.compliance_tags or [],
        "display_metadata": item.display_metadata or {},
        "created_at": item.created_at,
    }
