from sqlalchemy import Boolean, Column, Float, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID, TIMESTAMP
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
    confidence_score = Column(Numeric(4, 3), nullable=False, default=1.000)
    last_verified_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    verification_source = Column(String(32), nullable=False, default="seed")
    oos_30d_count = Column(Integer, nullable=False, default=0)
    node_type = Column(String(32), nullable=False, default="fc")
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FulfillmentNode(Base):
    __tablename__ = "fulfillment_nodes"
    __table_args__ = ({"schema": "inventory_svc"},)

    node_id = Column(String(64), primary_key=True)
    market_code = Column(String(16), nullable=False)
    node_name = Column(String(128), nullable=False)
    node_type = Column(String(32), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
