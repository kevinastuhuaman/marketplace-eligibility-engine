import uuid
from sqlalchemy import Column, String, Text, Integer, Boolean, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func
from app.db import Base


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"
    __table_args__ = {"schema": "eligibility_svc"}

    rule_id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String(100), nullable=False)
    rule_type = Column(String(30), nullable=False)  # geographic, temporal, category, seller, item, quantity
    action = Column(String(10), nullable=False, default="BLOCK")  # BLOCK, WARN, REQUIRE, GATE
    priority = Column(Integer, default=100)
    conflict_group = Column(String(50), nullable=True)
    market_codes = Column(ARRAY(Text), nullable=True)
    category_paths = Column(ARRAY(Text), nullable=True)
    compliance_tags = Column(ARRAY(Text), nullable=True)
    blocked_paths = Column(ARRAY(Text), nullable=True)
    rule_definition = Column(JSONB, nullable=False)
    reason = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSONB, default=dict)
    effective_from = Column(TIMESTAMP(timezone=True), server_default=func.now())
    effective_until = Column(TIMESTAMP(timezone=True), nullable=True)
    enabled = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
