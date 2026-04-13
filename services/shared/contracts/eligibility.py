"""Pydantic v2 models for the eligibility API -- THE PUBLIC CONTRACT."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CustomerLocation(BaseModel):
    state: str
    zip: str
    county: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    address_id: str | None = None


class EvaluationContext(BaseModel):
    customer_age: int | None = None
    requested_quantity: int | None = None
    background_check_status: str | None = None
    primary_node_id: str | None = None
    nearby_nodes: list[str] | None = None


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


class AlternativeNode(BaseModel):
    node_id: str
    node_name: str
    distance_miles: float
    available_qty: int
    confidence_score: float | None = None


class PathResult(BaseModel):
    path_code: str
    eligible: bool
    status: str  # "blocked", "gated", "conditional", "clear", "low_confidence"
    violations: list[Violation] = Field(default_factory=list)
    requirements: list[Requirement] = Field(default_factory=list)
    gates: list[Gate] = Field(default_factory=list)
    inventory_available: int | None = None
    confidence_score: float | None = None
    confidence_band: Literal["high", "medium", "low"] | None = None
    last_verified_at: datetime | None = None
    confidence_reason: str | None = None
    alternative_nodes: list[AlternativeNode] = Field(default_factory=list)
    matched_zone_codes: list[str] = Field(default_factory=list)
    zone_explanation: str | None = None
    fallback_applied: bool = False
    fallback_reason: str | None = None


class SellerSignal(BaseModel):
    ipi_score: int
    ipi_tier: str
    rank_adjustment_pct: float
    wfs_recommendation: str | None = None


class SellerPerformanceMetric(BaseModel):
    code: str
    label: str
    actual: float
    threshold: float
    direction: Literal["max", "min"]
    window_days: int
    status: Literal["meets_standard", "action_required"]
    recommendation: str
    wfs_assisted: bool = False


class SellerPerformanceSignal(BaseModel):
    overall_status: Literal["good_standing", "action_required"]
    pro_seller_eligible: bool
    uses_wfs: bool
    standards_last_updated: str
    account_risk: str
    source: str
    metrics: list[SellerPerformanceMetric] = Field(default_factory=list)


class MarketSummary(BaseModel):
    market_code: str
    display_name: str
    country_code: str
    region_code: str
    currency_code: str
    language_codes: list[str] = Field(default_factory=list)
    supported_paths: list[str] = Field(default_factory=list)
    regulatory_summary: dict[str, Any] = Field(default_factory=dict)


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
    seller_signal: SellerSignal | None = None
    seller_performance: SellerPerformanceSignal | None = None
    market_summary: MarketSummary | None = None


class DiagnosisRequest(EligibilityRequest):
    locale: Literal["auto", "en", "es"] = "auto"


class DiagnosisFinding(BaseModel):
    path_code: str
    source_service: str
    source_entity: str
    source_field: str
    rule_id: int | None = None
    rule_name: str | None = None
    cause_code: str
    root_cause: str
    explanation: str
    localized_explanation: str
    suggested_fix: str
    affected_items_estimate: int = 1
    severity: Literal["block", "gate", "warning"] = "block"


class TraceStep(BaseModel):
    step: int
    service: str
    operation: str
    request_summary: dict[str, Any] = Field(default_factory=dict)
    response_summary: dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = 0
    cache_hit: bool = False
    state: str | None = None


class DiagnosisResponse(BaseModel):
    evaluation: EligibilityResponse
    overall_status: str
    primary_finding: DiagnosisFinding | None = None
    findings: list[DiagnosisFinding] = Field(default_factory=list)
    suggested_fixes: list[str] = Field(default_factory=list)
    affected_items_estimate: int = 1
    trace: list[TraceStep] = Field(default_factory=list)
    generated_at: datetime


class MarketDefinition(BaseModel):
    market_code: str
    display_name: str
    country_code: str
    region_code: str
    currency_code: str
    language_codes: list[str] = Field(default_factory=list)
    supported_paths: list[str] = Field(default_factory=list)
    regulatory_summary: dict[str, Any] = Field(default_factory=dict)


class SellerIpiBreakdown(BaseModel):
    in_stock_rate: float
    defect_rate: float
    on_time_rate: float
    cancellation_rate: float


class SellerIpiResponse(BaseModel):
    seller_id: UUID
    seller_name: str
    ipi_score: int
    tier: str
    breakdown: SellerIpiBreakdown
    rank_adjustment_pct: float
    wfs_recommendation: str | None = None


class SellerPerformanceResponse(BaseModel):
    seller_id: UUID
    seller_name: str
    overall_status: Literal["good_standing", "action_required"]
    pro_seller_eligible: bool
    uses_wfs: bool
    standards_last_updated: str
    account_risk: str
    source: str
    metrics: list[SellerPerformanceMetric] = Field(default_factory=list)


class CircuitBreakerStatus(BaseModel):
    service: str
    state: Literal["closed", "open", "half_open"]
    failure_count: int = 0
    last_failure_at: datetime | None = None
    last_success_at: datetime | None = None
    opened_at: datetime | None = None
    fallback_mode: str
    recent_events: list[dict[str, Any]] = Field(default_factory=list)


class CircuitBreakerResponse(BaseModel):
    breakers: list[CircuitBreakerStatus] = Field(default_factory=list)


class BatchEvaluateRequest(BaseModel):
    requests: list[EligibilityRequest] = Field(default_factory=list, max_length=100)


class BatchEvaluateResponse(BaseModel):
    results: list[EligibilityResponse] = Field(default_factory=list)
    total_requests: int = 0
    succeeded: int = 0
    failed: int = 0
    total_ms: int = 0
    p50_ms: float = 0
    p95_ms: float = 0
    p99_ms: float = 0


class ServiceUnavailableResponse(BaseModel):
    error: str = "service_unavailable"
    detail: str
    retry_after_seconds: int = 5
