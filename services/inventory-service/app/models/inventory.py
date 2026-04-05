import uuid

from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db import Base


class InventoryPosition(Base):
    __tablename__ = "inventory_positions"
    __table_args__ = ({"schema": "inventory_svc"},)

    item_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    fulfillment_node = Column(String(50), nullable=False, primary_key=True)
    path_id = Column(Integer, nullable=False, primary_key=True)
    seller_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    available_qty = Column(Integer, default=0)
    reserved_qty = Column(Integer, default=0)
    node_enabled = Column(Boolean, default=True)
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )
