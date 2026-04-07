"""Pydantic v2 models for the eligibility API -- THE PUBLIC CONTRACT."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CustomerLocation(BaseModel):
    state: str
    zip: str
    county: str | None = None


class EvaluationContext(BaseModel):
    customer_age: int | None = None
    requested_quantity: int | None = None
    background_check_status: str | None = None


class EligibilityRequest(BaseModel):
    item_id: UUID
    market_code: str
    customer_location: CustomerLocation
    seller_id: UUID | None = None
    timestamp: datetime
    context: EvaluationContext | None = None


class Violation(BaseModel):
    rule_id: int
    rule_name: str
    action: str  # "BLOCK"
    reason: str
    priority: int
    metadata: dict = Field(default_factory=dict)


class Requirement(BaseModel):
    rule_id: int
    rule_name: str
    action: str  # "REQUIRE"
    reason: str
    priority: int
    satisfied: bool
    requirement_type: str  # "age_verification", "background_check", "id_verification"
    parameters: dict = Field(default_factory=dict)  # e.g. {"minimum_age": 21}
    metadata: dict = Field(default_factory=dict)


class Gate(BaseModel):
    rule_id: int
    rule_name: str
    action: str  # "GATE"
    reason: str
    priority: int
    gate_type: str  # "metric_threshold", "trust_tier"
    current: dict = Field(default_factory=dict)  # current seller values
    required: dict = Field(default_factory=dict)  # threshold requirements
    gap: dict = Field(default_factory=dict)  # difference (what to improve)
    metadata: dict = Field(default_factory=dict)


class Warning(BaseModel):
    rule_id: int
    rule_name: str
    action: str  # "WARN"
    reason: str
    priority: int
    metadata: dict = Field(default_factory=dict)


class ConflictResolution(BaseModel):
    winner_rule_id: int
    winner_rule_name: str
    suppressed_rule_id: int
    suppressed_rule_name: str
    reason: str


class PathResult(BaseModel):
    path_code: str
    eligible: bool
    status: str  # "blocked", "gated", "conditional", "clear"
    violations: list[Violation] = Field(default_factory=list)
    requirements: list[Requirement] = Field(default_factory=list)
    gates: list[Gate] = Field(default_factory=list)
    inventory_available: int | None = None


class EligibilityResponse(BaseModel):
    item_id: UUID
    market_code: str
    eligible: bool
    paths: list[PathResult] = Field(default_factory=list)
    warnings: list[Warning] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    conflict_resolutions: list[ConflictResolution] = Field(default_factory=list)
    rules_evaluated: int = 0
    rules_suppressed: int = 0
    rules_loaded: int = 0
    debug: dict | None = None
    evaluation_ms: int = 0
    evaluated_at: datetime


class ServiceUnavailableResponse(BaseModel):
    error: str = "service_unavailable"
    detail: str
    retry_after_seconds: int = 5
