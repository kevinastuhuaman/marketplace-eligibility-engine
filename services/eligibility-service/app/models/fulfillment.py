from sqlalchemy import Column, String, Text, Integer, Boolean, Numeric
from app.db import Base


class FulfillmentPath(Base):
    __tablename__ = "fulfillment_paths"
    __table_args__ = {"schema": "eligibility_svc"}

    path_id = Column(Integer, primary_key=True, autoincrement=True)
    path_code = Column(String(50), unique=True, nullable=False)
    display_name = Column(Text, nullable=False)
    owner = Column(String(5), nullable=False)  # '1p' or '3p'
    requires_inventory = Column(Boolean, default=True)
    max_weight_lbs = Column(Numeric, nullable=True)


class MarketFulfillment(Base):
    __tablename__ = "market_fulfillment"
    __table_args__ = {"schema": "eligibility_svc"}

    market_code = Column(String(10), primary_key=True)
    path_id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
