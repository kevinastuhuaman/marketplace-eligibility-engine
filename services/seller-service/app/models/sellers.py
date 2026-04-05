import uuid

from sqlalchemy import Column, String, Text, Integer, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
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
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
