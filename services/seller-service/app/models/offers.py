import uuid

from sqlalchemy import Column, Boolean
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db import Base


class SellerOffer(Base):
    __tablename__ = "seller_offers"
    __table_args__ = {"schema": "seller_svc"}

    seller_id = Column(UUID(as_uuid=True), primary_key=True)
    item_id = Column(UUID(as_uuid=True), primary_key=True)
    active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
