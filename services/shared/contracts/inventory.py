"""Pydantic v2 models for inventory-service responses."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class NodeAvailability(BaseModel):
    fulfillment_node: str
    available_qty: int
    reserved_qty: int
    sellable_qty: int  # available - reserved
    node_enabled: bool


class PathAvailability(BaseModel):
    path_id: int
    path_code: str
    total_sellable: int  # sum across all enabled nodes
    nodes: list[NodeAvailability]


class AvailabilityResponse(BaseModel):
    item_id: UUID
    seller_id: UUID
    paths: list[PathAvailability]
