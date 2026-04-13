from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class RuleCreate(BaseModel):
    rule_name: str
    rule_type: str
    regulation_type: str = "GENERAL"
    action: str = "BLOCK"
    priority: int = 100
    conflict_group: str | None = None
    market_codes: list[str] | None = None
    category_paths: list[str] | None = None
    compliance_tags: list[str] | None = None
    blocked_paths: list[str] | None = None
    rule_definition: dict
    reason: str
    metadata: dict | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    enabled: bool | None = True


class FulfillmentPathCreate(BaseModel):
    path_code: str
    display_name: str
    owner: str  # "1p" or "3p"
    requires_inventory: bool = True
    max_weight_lbs: Decimal | None = None


class MarketFulfillmentCreate(BaseModel):
    market_code: str
    path_id: int
    enabled: bool = True
    priority: int = 0


class MarketRegulationCreate(BaseModel):
    market_code: str
    display_name: str
    country_code: str
    region_code: str
    currency_code: str = "USD"
    language_codes: list[str] | None = None
    default_timezone: str = "America/Los_Angeles"
    regulatory_summary: dict | None = None
    active: bool = True


class GeoRestrictionZoneCreate(BaseModel):
    zone_code: str
    market_code: str
    zone_name: str
    zone_type: str
    geometry_type: str = "polygon"
    center_latitude: float | None = None
    center_longitude: float | None = None
    radius_meters: int | None = None
    polygon_coordinates: list | None = None
    hex_cells: list[str] | None = None
    blocked_paths: list[str] | None = None
    metadata: dict | None = None
    active: bool = True
