import uuid

from sqlalchemy import Boolean, Column, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db import Base


class Seller(Base):
    __tablename__ = "sellers"
    __table_args__ = {"schema": "seller_svc"}

    seller_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    trust_tier = Column(String(20), default="new")
    defect_rate = Column(Numeric, default=0)
    return_rate = Column(Numeric, default=0)
    on_time_rate = Column(Numeric, default=1.0)
    total_orders = Column(Integer, default=0)
    in_stock_rate = Column(Numeric, default=0.98)
    cancellation_rate = Column(Numeric, default=0.01)
    valid_tracking_rate = Column(Numeric, default=0.99)
    seller_response_rate = Column(Numeric, default=0.95)
    item_not_received_rate = Column(Numeric, default=0.01)
    negative_feedback_rate = Column(Numeric, default=0.01)
    uses_wfs = Column(Boolean, default=False)
    vat_registered = Column(Boolean, default=False)
    ipi_score = Column(Integer, default=850)
    ipi_breakdown = Column(JSONB, default=dict)
    ipi_updated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    performance_updated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
