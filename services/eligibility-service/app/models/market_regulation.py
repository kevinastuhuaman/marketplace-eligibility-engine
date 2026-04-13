from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.sql import func

from app.db import Base


class MarketRegulation(Base):
    __tablename__ = "market_regulations"
    __table_args__ = {"schema": "eligibility_svc"}

    market_code = Column(String(16), primary_key=True)
    display_name = Column(String(128), nullable=False)
    country_code = Column(String(2), nullable=False)
    region_code = Column(String(16), nullable=False)
    currency_code = Column(String(3), nullable=False, default="USD")
    language_codes = Column(JSONB, default=list)
    default_timezone = Column(String(64), nullable=False)
    regulatory_summary = Column(JSONB, default=dict)
    active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )
