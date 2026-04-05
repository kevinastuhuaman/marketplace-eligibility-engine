from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal


class SellerCreate(BaseModel):
    seller_id: UUID | None = None  # Allow explicit UUID for seeding (Walmart)
    name: str
    trust_tier: str = "new"
    defect_rate: Decimal = Decimal("0")
    return_rate: Decimal = Decimal("0")
    on_time_rate: Decimal = Decimal("1.0")
    total_orders: int = 0


class OfferCreate(BaseModel):
    seller_id: UUID
    item_id: UUID
    active: bool = True
