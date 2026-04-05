"""Pydantic v2 models for item-service responses."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ItemResponse(BaseModel):
    item_id: UUID
    sku: str
    name: str
    item_type: str
    category_path: str | None
    attributes: dict
    compliance_tags: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}
