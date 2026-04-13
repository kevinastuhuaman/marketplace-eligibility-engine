from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal


class SellerCreate(BaseModel):
    seller_id: UUID | None = None  # Allow explicit UUID for seeding (platform 1P seller)
    name: str
    trust_tier: str = "new"
    defect_rate: Decimal = Decimal("0")
    return_rate: Decimal = Decimal("0")
    on_time_rate: Decimal = Decimal("1.0")
    total_orders: int = 0
    in_stock_rate: Decimal = Decimal("0.98")
    cancellation_rate: Decimal = Decimal("0.01")
    valid_tracking_rate: Decimal = Decimal("0.99")
    seller_response_rate: Decimal = Decimal("0.95")
    item_not_received_rate: Decimal = Decimal("0.01")
    negative_feedback_rate: Decimal = Decimal("0.01")
    uses_wfs: bool = False
    vat_registered: bool = False
    ipi_score: int = 850
    ipi_breakdown: dict | None = None


class MetricsUpdate(BaseModel):
    defect_rate: Decimal | None = None
    return_rate: Decimal | None = None
    on_time_rate: Decimal | None = None
    total_orders: int | None = None
    in_stock_rate: Decimal | None = None
    cancellation_rate: Decimal | None = None
    valid_tracking_rate: Decimal | None = None
    seller_response_rate: Decimal | None = None
    item_not_received_rate: Decimal | None = None
    negative_feedback_rate: Decimal | None = None
    uses_wfs: bool | None = None
    vat_registered: bool | None = None
    ipi_score: int | None = None
    ipi_breakdown: dict | None = None


class OfferCreate(BaseModel):
    item_id: UUID
    active: bool = True
