"""Pydantic v2 models for seller-service responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class SellerResponse(BaseModel):
    seller_id: UUID
    name: str
    trust_tier: str
    defect_rate: Decimal
    return_rate: Decimal
    on_time_rate: Decimal
    total_orders: int
    created_at: datetime

    model_config = {"from_attributes": True}


class OfferCheckResponse(BaseModel):
    seller_id: UUID
    item_id: UUID
    active: bool
    exists: bool  # False if no row found at all
