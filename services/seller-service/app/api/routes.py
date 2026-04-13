from __future__ import annotations

from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.offers import SellerOffer
from app.models.sellers import Seller
from app.schemas.sellers import MetricsUpdate, OfferCreate, SellerCreate
from app.services.ipi_service import compute_ipi, ipi_tier, rank_adjustment_pct
from app.services.performance_service import build_performance_snapshot
from shared.constants import PLATFORM_SELLER_ID

router = APIRouter()
PACIFIC = ZoneInfo("America/Los_Angeles")


def _serialize_seller(seller: Seller) -> dict:
    performance = build_performance_snapshot(seller)
    return {
        "seller_id": seller.seller_id,
        "name": seller.name,
        "trust_tier": seller.trust_tier,
        "defect_rate": float(seller.defect_rate),
        "return_rate": float(seller.return_rate),
        "on_time_rate": float(seller.on_time_rate),
        "on_time_delivery_rate": float(seller.on_time_rate),
        "total_orders": seller.total_orders,
        "in_stock_rate": float(seller.in_stock_rate),
        "cancellation_rate": float(seller.cancellation_rate),
        "valid_tracking_rate": float(seller.valid_tracking_rate),
        "seller_response_rate": float(seller.seller_response_rate),
        "item_not_received_rate": float(seller.item_not_received_rate),
        "negative_feedback_rate": float(seller.negative_feedback_rate),
        "uses_wfs": bool(seller.uses_wfs),
        "vat_registered": bool(seller.vat_registered),
        "ipi_score": seller.ipi_score,
        "ipi_breakdown": seller.ipi_breakdown or {},
        "performance_status": performance["overall_status"],
        "pro_seller_eligible": performance["pro_seller_eligible"],
        "seller_performance": performance,
        "created_at": seller.created_at,
    }


@router.get("/v1/sellers")
async def list_sellers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Seller).where(Seller.seller_id != PLATFORM_SELLER_ID).order_by(Seller.name)
    )
    return [_serialize_seller(seller) for seller in result.scalars().all()]


@router.get("/v1/sellers/for-item/{item_id}")
async def sellers_for_item(item_id: UUID, db: AsyncSession = Depends(get_db)):
    offers_result = await db.execute(
        select(SellerOffer).where(
            and_(
                SellerOffer.item_id == item_id,
                SellerOffer.active.is_(True),
                SellerOffer.seller_id != PLATFORM_SELLER_ID,
            )
        )
    )
    offers = offers_result.scalars().all()
    if not offers:
        return []
    seller_ids = list({offer.seller_id for offer in offers})
    sellers_result = await db.execute(select(Seller).where(Seller.seller_id.in_(seller_ids)))
    sellers = {seller.seller_id: seller for seller in sellers_result.scalars().all()}
    response = []
    for seller_id in seller_ids:
        if seller_id not in sellers:
            continue
        seller = sellers[seller_id]
        performance = build_performance_snapshot(seller)
        response.append(
            {
                "seller_id": str(seller_id),
                "name": seller.name,
                "trust_tier": seller.trust_tier,
                "defect_rate": float(seller.defect_rate),
                "ipi_score": seller.ipi_score,
                "performance_status": performance["overall_status"],
                "pro_seller_eligible": performance["pro_seller_eligible"],
                "uses_wfs": bool(seller.uses_wfs),
            }
        )
    return response


@router.get("/v1/sellers/{seller_id}")
async def get_seller(seller_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Seller).where(Seller.seller_id == seller_id))
    seller = result.scalar_one_or_none()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    return _serialize_seller(seller)


@router.get("/v1/sellers/{seller_id}/ipi")
async def get_seller_ipi(seller_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Seller).where(Seller.seller_id == seller_id))
    seller = result.scalar_one_or_none()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    score = seller.ipi_score
    return {
        "seller_id": seller.seller_id,
        "seller_name": seller.name,
        "ipi_score": score,
        "tier": ipi_tier(score),
        "breakdown": seller.ipi_breakdown
        or {
            "in_stock_rate": float(seller.in_stock_rate),
            "defect_rate": float(seller.defect_rate),
            "on_time_rate": float(seller.on_time_rate),
            "cancellation_rate": float(seller.cancellation_rate),
        },
        "rank_adjustment_pct": rank_adjustment_pct(score),
        "wfs_recommendation": (
            f"This seller's IPI is {score} — recommend WFS for reliability."
            if score < 300
            else None
        ),
    }


@router.get("/v1/sellers/{seller_id}/performance")
async def get_seller_performance(seller_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Seller).where(Seller.seller_id == seller_id))
    seller = result.scalar_one_or_none()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    return build_performance_snapshot(seller)


@router.get("/v1/sellers/{seller_id}/offers/{item_id}")
async def check_offer(seller_id: UUID, item_id: UUID, db: AsyncSession = Depends(get_db)):
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
async def create_seller(payload: SellerCreate, request: Request, db: AsyncSession = Depends(get_db)):
    score, breakdown = compute_ipi(
        in_stock_rate=float(payload.in_stock_rate),
        defect_rate=float(payload.defect_rate),
        on_time_rate=float(payload.on_time_rate),
        cancellation_rate=float(payload.cancellation_rate),
    )
    seller = Seller(
        seller_id=payload.seller_id if payload.seller_id else None,
        name=payload.name,
        trust_tier=payload.trust_tier,
        defect_rate=payload.defect_rate,
        return_rate=payload.return_rate,
        on_time_rate=payload.on_time_rate,
        total_orders=payload.total_orders,
        in_stock_rate=payload.in_stock_rate,
        cancellation_rate=payload.cancellation_rate,
        valid_tracking_rate=payload.valid_tracking_rate,
        seller_response_rate=payload.seller_response_rate,
        item_not_received_rate=payload.item_not_received_rate,
        negative_feedback_rate=payload.negative_feedback_rate,
        uses_wfs=payload.uses_wfs,
        vat_registered=payload.vat_registered,
        ipi_score=payload.ipi_score if payload.ipi_score is not None else score,
        ipi_breakdown=payload.ipi_breakdown if payload.ipi_breakdown is not None else breakdown,
        ipi_updated_at=datetime.now(PACIFIC),
        performance_updated_at=datetime.now(PACIFIC),
    )
    db.add(seller)
    await db.commit()
    await db.refresh(seller)

    publisher = getattr(request.app.state, "stream_publisher", None)
    if publisher:
        await publisher.publish(
            "seller_created",
            {
                "seller_id": str(seller.seller_id),
                "name": seller.name,
                "trust_tier": seller.trust_tier,
                "ipi_score": seller.ipi_score,
            },
        )
    return {"seller_id": seller.seller_id, "name": seller.name}


@router.put("/v1/sellers/{seller_id}/metrics")
async def update_metrics(
    seller_id: UUID,
    payload: MetricsUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Seller).where(Seller.seller_id == seller_id))
    seller = result.scalar_one_or_none()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    if payload.defect_rate is not None:
        seller.defect_rate = payload.defect_rate
    if payload.return_rate is not None:
        seller.return_rate = payload.return_rate
    if payload.on_time_rate is not None:
        seller.on_time_rate = payload.on_time_rate
    if payload.total_orders is not None:
        seller.total_orders = payload.total_orders
    if payload.in_stock_rate is not None:
        seller.in_stock_rate = payload.in_stock_rate
    if payload.cancellation_rate is not None:
        seller.cancellation_rate = payload.cancellation_rate
    if payload.valid_tracking_rate is not None:
        seller.valid_tracking_rate = payload.valid_tracking_rate
    if payload.seller_response_rate is not None:
        seller.seller_response_rate = payload.seller_response_rate
    if payload.item_not_received_rate is not None:
        seller.item_not_received_rate = payload.item_not_received_rate
    if payload.negative_feedback_rate is not None:
        seller.negative_feedback_rate = payload.negative_feedback_rate
    if payload.uses_wfs is not None:
        seller.uses_wfs = payload.uses_wfs
    if payload.vat_registered is not None:
        seller.vat_registered = payload.vat_registered

    score, breakdown = compute_ipi(
        in_stock_rate=float(seller.in_stock_rate),
        defect_rate=float(seller.defect_rate),
        on_time_rate=float(seller.on_time_rate),
        cancellation_rate=float(seller.cancellation_rate),
    )
    seller.ipi_score = payload.ipi_score if payload.ipi_score is not None else score
    seller.ipi_breakdown = payload.ipi_breakdown if payload.ipi_breakdown is not None else breakdown
    seller.ipi_updated_at = datetime.now(PACIFIC)
    seller.performance_updated_at = datetime.now(PACIFIC)
    await db.commit()
    await db.refresh(seller)

    publisher = getattr(request.app.state, "stream_publisher", None)
    if publisher:
        await publisher.publish(
            "metrics_updated",
            {
                "seller_id": str(seller.seller_id),
                "defect_rate": float(seller.defect_rate),
                "return_rate": float(seller.return_rate),
                "on_time_rate": float(seller.on_time_rate),
                "total_orders": seller.total_orders,
                "in_stock_rate": float(seller.in_stock_rate),
                "cancellation_rate": float(seller.cancellation_rate),
                "valid_tracking_rate": float(seller.valid_tracking_rate),
                "seller_response_rate": float(seller.seller_response_rate),
                "item_not_received_rate": float(seller.item_not_received_rate),
                "negative_feedback_rate": float(seller.negative_feedback_rate),
                "uses_wfs": bool(seller.uses_wfs),
                "ipi_score": seller.ipi_score,
            },
        )
    return {"seller_id": seller.seller_id, "status": "updated"}


@router.post("/v1/sellers/{seller_id}/offers", status_code=201)
async def create_offer(
    seller_id: UUID,
    payload: OfferCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    offer = SellerOffer(seller_id=seller_id, item_id=payload.item_id, active=payload.active)
    db.add(offer)
    await db.commit()
    publisher = getattr(request.app.state, "stream_publisher", None)
    if publisher:
        await publisher.publish(
            "offer_activated",
            {
                "seller_id": str(seller_id),
                "item_id": str(payload.item_id),
                "active": payload.active,
            },
        )
    return {
        "seller_id": str(seller_id),
        "item_id": str(payload.item_id),
        "active": payload.active,
    }


@router.get("/v1/sellers/{seller_id}/offers")
async def list_offers(seller_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SellerOffer).where(SellerOffer.seller_id == seller_id))
    offers = result.scalars().all()
    return [
        {"seller_id": str(offer.seller_id), "item_id": str(offer.item_id), "active": offer.active}
        for offer in offers
    ]
