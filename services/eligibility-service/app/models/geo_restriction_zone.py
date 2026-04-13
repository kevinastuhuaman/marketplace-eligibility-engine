from sqlalchemy import Boolean, Column, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.sql import func

from app.db import Base


class GeoRestrictionZone(Base):
    __tablename__ = "geo_restriction_zones"
    __table_args__ = {"schema": "eligibility_svc"}

    zone_id = Column(Integer, primary_key=True, autoincrement=True)
    zone_code = Column(String(64), nullable=False, unique=True)
    market_code = Column(String(16), nullable=False)
    zone_name = Column(String(128), nullable=False)
    zone_type = Column(String(32), nullable=False)
    geometry_type = Column(String(16), nullable=False, default="polygon")
    center_latitude = Column(Float, nullable=True)
    center_longitude = Column(Float, nullable=True)
    radius_meters = Column(Integer, nullable=True)
    polygon_coordinates = Column(JSONB, default=list)
    hex_cells = Column(JSONB, default=list)
    blocked_paths = Column(JSONB, default=list)
    metadata_ = Column("metadata", JSONB, default=dict)
    active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )
