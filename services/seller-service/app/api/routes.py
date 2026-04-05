from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db import get_db
from app.models.sellers import Seller
from app.models.offers import SellerOffer
from app.schemas.sellers import SellerCreate, OfferCreate

router = APIRouter()


@router.get("/v1/sellers/{seller_id}")
async def get_seller(seller_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Seller).where(Seller.seller_id == seller_id))
    seller = result.scalar_one_or_none()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    return {
        "seller_id": seller.seller_id,
        "name": seller.name,
        "trust_tier": seller.trust_tier,
        "defect_rate": seller.defect_rate,
        "return_rate": seller.return_rate,
        "on_time_rate": seller.on_time_rate,
        "total_orders": seller.total_orders,
        "created_at": seller.created_at,
    }


@router.get("/v1/sellers/{seller_id}/offers/{item_id}")
async def check_offer(
    seller_id: UUID, item_id: UUID, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SellerOffer).where(
            and_(SellerOffer.seller_id == seller_id, SellerOffer.item_id == item_id)
        )
    )
    offer = result.scalar_one_or_none()
    if not offer:
        return {
            "seller_id": str(seller_id),
            "item_id": str(item_id),
            "active": False,
            "exists": False,
        }
    return {
        "seller_id": str(seller_id),
        "item_id": str(item_id),
        "active": offer.active,
        "exists": True,
    }


@router.post("/v1/sellers", status_code=201)
async def create_seller(
    payload: SellerCreate, request: Request, db: AsyncSession = Depends(get_db)
):
    seller = Seller(
        seller_id=payload.seller_id if payload.seller_id else None,
        name=payload.name,
        trust_tier=payload.trust_tier,
        defect_rate=payload.defect_rate,
        return_rate=payload.return_rate,
        on_time_rate=payload.on_time_rate,
        total_orders=payload.total_orders,
    )
    db.add(seller)
    await db.commit()
    await db.refresh(seller)

    # Publish to Redis Stream
    publisher = request.app.state.stream_publisher
    if publisher:
        await publisher.publish("seller_created", {
            "seller_id": str(seller.seller_id),
            "name": seller.name,
            "trust_tier": seller.trust_tier,
        })

    return {"seller_id": seller.seller_id, "name": seller.name}


@router.post("/v1/sellers/{seller_id}/offers", status_code=201)
async def create_offer(
    seller_id: UUID, payload: OfferCreate, db: AsyncSession = Depends(get_db)
):
    offer = SellerOffer(
        seller_id=seller_id, item_id=payload.item_id, active=payload.active
    )
    db.add(offer)
    await db.commit()
    return {
        "seller_id": str(seller_id),
        "item_id": str(payload.item_id),
        "active": payload.active,
    }


@router.get("/v1/sellers/{seller_id}/offers")
async def list_offers(seller_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SellerOffer).where(SellerOffer.seller_id == seller_id)
    )
    offers = result.scalars().all()
    return [
        {"seller_id": str(o.seller_id), "item_id": str(o.item_id), "active": o.active}
        for o in offers
    ]
