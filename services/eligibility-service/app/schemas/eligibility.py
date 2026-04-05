from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class RuleCreate(BaseModel):
    rule_name: str
    rule_type: str
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
