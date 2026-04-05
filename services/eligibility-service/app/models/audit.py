from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func
from app.db import Base


class EligibilityAuditLog(Base):
    __tablename__ = "eligibility_audit_log"
    __table_args__ = {"schema": "eligibility_svc"}

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(UUID(as_uuid=True), nullable=False)
    market_code = Column(String(10), nullable=False)
    seller_id = Column(UUID(as_uuid=True), nullable=True)
    eligible = Column(Boolean, nullable=False)
    request_payload = Column(JSONB, nullable=False)
    response_payload = Column(JSONB, nullable=False)
    rules_evaluated = Column(Integer, nullable=False)
    rules_suppressed = Column(Integer, default=0)
    evaluation_ms = Column(Integer, nullable=False)
    evaluated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
