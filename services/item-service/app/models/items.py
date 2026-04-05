import uuid

from sqlalchemy import Column, String, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy_utils import LtreeType

from app.db import Base


class Item(Base):
    __tablename__ = "items"
    __table_args__ = {"schema": "item_svc"}

    item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(Text, nullable=False)
    item_type = Column(String(20), default="base")
    category_path = Column(LtreeType, nullable=True)
    attributes = Column(JSONB, default=dict)
    compliance_tags = Column(ARRAY(Text), default=list)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
