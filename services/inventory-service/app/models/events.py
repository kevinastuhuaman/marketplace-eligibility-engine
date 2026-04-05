import uuid

from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db import Base


class InventoryEvent(Base):
    __tablename__ = "inventory_events"
    __table_args__ = {"schema": "inventory_svc"}

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(30), nullable=False)
    item_id = Column(UUID(as_uuid=True), nullable=False)
    fulfillment_node = Column(String(50))
    path_id = Column(Integer)
    seller_id = Column(UUID(as_uuid=True))
    delta = Column(Integer)
    new_available_qty = Column(Integer)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now())
