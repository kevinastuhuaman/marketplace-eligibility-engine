from pydantic import BaseModel
from uuid import UUID


class PositionCreate(BaseModel):
    item_id: UUID
    fulfillment_node: str
    path_id: int
    seller_id: UUID
    available_qty: int = 0
    reserved_qty: int = 0
    node_enabled: bool = True


class EventCreate(BaseModel):
    item_id: UUID
    fulfillment_node: str
    event_type: str
    path_id: int | None = None
    seller_id: UUID | None = None
    delta: int | None = None
