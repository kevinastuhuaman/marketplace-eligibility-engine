from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PositionCreate(BaseModel):
    item_id: UUID
    fulfillment_node: str
    path_id: int
    seller_id: UUID
    available_qty: int = 0
    reserved_qty: int = 0
    node_enabled: bool = True
    confidence_score: Decimal = Decimal("1.000")
    last_verified_at: datetime | None = None
    verification_source: str = "seed"
    oos_30d_count: int = 0
    node_type: str = "fc"


class EventCreate(BaseModel):
    item_id: UUID
    fulfillment_node: str
    event_type: str
    path_id: int | None = None
    seller_id: UUID | None = None
    delta: int | None = None


class FulfillmentNodeCreate(BaseModel):
    node_id: str
    market_code: str
    node_name: str
    node_type: str
    latitude: float
    longitude: float
    enabled: bool = True
    metadata: dict = Field(default_factory=dict)
