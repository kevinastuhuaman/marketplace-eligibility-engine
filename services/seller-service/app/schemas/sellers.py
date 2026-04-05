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


class MetricsUpdate(BaseModel):
    defect_rate: Decimal | None = None
    return_rate: Decimal | None = None
    on_time_rate: Decimal | None = None
    total_orders: int | None = None


class OfferCreate(BaseModel):
    item_id: UUID
    active: bool = True
