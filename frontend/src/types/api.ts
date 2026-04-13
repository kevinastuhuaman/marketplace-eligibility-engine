export type EvaluationStatus =
  | "blocked"
  | "gated"
  | "conditional"
  | "clear"
  | "low_confidence";

export type DiagnosisLocale = "auto" | "en" | "es";
export type ConfidenceBand = "high" | "medium" | "low";

export interface Item {
  item_id: string;
  sku: string;
  name: string;
  item_type: string;
  category_path: string | null;
  attributes: Record<string, unknown>;
  compliance_tags: string[];
  display_metadata: {
    price?: string;
    emoji?: string;
    description?: string;
  };
  created_at: string;
}

export interface CustomerLocation {
  state: string;
  zip: string;
  county?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  address_id?: string | null;
}

export interface EvaluationContext {
  customer_age?: number;
  requested_quantity?: number;
  background_check_status?: "clear" | "pending" | "failed";
  primary_node_id?: string | null;
  nearby_nodes?: string[];
}

export interface EvaluateRequest {
  item_id: string;
  market_code: string;
  customer_location: CustomerLocation;
  seller_id?: string | null;
  timestamp: string;
  context?: EvaluationContext;
}

export interface AlternativeNode {
  node_id: string;
  node_name: string;
  distance_miles: number;
  available_qty: number;
}

export interface SellerSignal {
  ipi_score: number;
  ipi_tier: string;
  rank_adjustment_pct: number;
  wfs_recommendation?: string | null;
}

export type SellerPerformanceStatus = "good_standing" | "action_required";
export type SellerPerformanceMetricStatus = "meets_standard" | "action_required";

export interface SellerPerformanceMetric {
  code: string;
  label: string;
  actual: number;
  threshold: number;
  direction: "max" | "min";
  window_days: number;
  status: SellerPerformanceMetricStatus;
  recommendation: string;
  wfs_assisted: boolean;
}

export interface SellerPerformanceSignal {
  overall_status: SellerPerformanceStatus;
  pro_seller_eligible: boolean;
  uses_wfs: boolean;
  standards_last_updated: string;
  account_risk: string;
  source: string;
  metrics: SellerPerformanceMetric[];
}

export interface MarketSummary {
  market_code: string;
  display_name: string;
  country_code: string;
  region_code: string;
  currency_code: string;
  language_codes: string[];
  supported_paths: string[];
  regulatory_summary: Record<string, unknown>;
}

interface BaseRuleOutcome {
  rule_id: number;
  rule_name: string;
  action: string;
  reason: string;
  priority: number;
  metadata: Record<string, unknown>;
}

export interface Violation extends BaseRuleOutcome {}

export interface Requirement extends BaseRuleOutcome {
  satisfied: boolean;
  requirement_type: string;
  parameters: Record<string, unknown>;
}

export interface Gate extends BaseRuleOutcome {
  gate_type: string;
  current: Record<string, unknown>;
  required: Record<string, unknown>;
  gap: Record<string, unknown>;
}

export interface Warning extends BaseRuleOutcome {}

export interface ConflictResolution {
  winner_rule_id: number;
  winner_rule_name: string;
  suppressed_rule_id: number;
  suppressed_rule_name: string;
  reason: string;
}

export interface PathResult {
  path_code: string;
  eligible: boolean;
  status: EvaluationStatus;
  violations: Violation[];
  requirements: Requirement[];
  gates: Gate[];
  inventory_available: number | null;
  confidence_score?: number | null;
  confidence_band?: ConfidenceBand | null;
  confidence_reason?: string | null;
  last_verified_at?: string | null;
  alternative_nodes: AlternativeNode[];
  matched_zone_codes: string[];
  zone_explanation?: string | null;
  fallback_applied: boolean;
  fallback_reason?: string | null;
}

export interface DebugRule {
  rule_id: number;
  rule_name: string;
  rule_type: string;
  action: "BLOCK" | "GATE" | "REQUIRE" | "WARN";
  priority: number;
  conflict_group: string | null;
  blocked_paths: string[];
  reason: string;
  rule_definition: Record<string, unknown>;
  matched: boolean;
  suppressed: boolean;
  suppressed_by: { rule_id: number; rule_name: string } | null;
  survived: boolean;
}

export interface DebugPathEvaluation {
  path_code: string;
  rules: DebugRule[];
}

export interface DebugInfo {
  rules_loaded: number;
  rules_triggered: number;
  rules_suppressed: number;
  per_path_evaluations: DebugPathEvaluation[];
}

export interface EligibilityResponse {
  item_id: string;
  market_code: string;
  eligible: boolean;
  paths: PathResult[];
  warnings: Warning[];
  errors: string[];
  conflict_resolutions: ConflictResolution[];
  rules_evaluated: number;
  rules_suppressed: number;
  rules_loaded: number;
  evaluation_ms: number;
  evaluated_at: string;
  seller_signal?: SellerSignal | null;
  seller_performance?: SellerPerformanceSignal | null;
  market_summary?: MarketSummary | null;
  debug: DebugInfo | null;
}

export interface SellerInfo {
  seller_id: string;
  name: string;
  trust_tier: string;
  defect_rate: number;
  ipi_score?: number | null;
  performance_status?: SellerPerformanceStatus;
  pro_seller_eligible?: boolean;
  uses_wfs?: boolean;
}

export interface SellerIpiBreakdown {
  in_stock_rate?: number;
  defect_rate?: number;
  on_time_rate?: number;
  cancellation_rate?: number;
}

export interface SellerIpiResponse {
  seller_id: string;
  seller_name: string;
  ipi_score: number;
  tier: string;
  breakdown: SellerIpiBreakdown;
  rank_adjustment_pct: number;
  wfs_recommendation?: string | null;
}

export interface SellerPerformanceResponse {
  seller_id: string;
  seller_name: string;
  overall_status: SellerPerformanceStatus;
  pro_seller_eligible: boolean;
  uses_wfs: boolean;
  standards_last_updated: string;
  account_risk: string;
  source: string;
  metrics: SellerPerformanceMetric[];
}

export interface TraceStep {
  step: number;
  service: string;
  operation: string;
  request_summary?: Record<string, unknown>;
  response_summary?: Record<string, unknown>;
  duration_ms?: number | null;
  cache_hit?: boolean;
  state?: string | null;
}

export interface DiagnosisFinding {
  path_code: string;
  source_service: string;
  source_entity: string;
  source_field: string;
  rule_id?: number | null;
  rule_name?: string | null;
  cause_code: string;
  root_cause: string;
  explanation: string;
  localized_explanation: string;
  suggested_fix?: string | null;
  affected_items_estimate: number;
}

export interface DiagnosisRequest extends EvaluateRequest {
  locale?: DiagnosisLocale;
}

export interface DiagnosisResponse {
  evaluation: EligibilityResponse;
  overall_status: EvaluationStatus;
  primary_finding?: DiagnosisFinding | null;
  findings: DiagnosisFinding[];
  suggested_fixes: string[];
  affected_items_estimate: number;
  trace: TraceStep[];
  generated_at: string;
}

export interface MarketDefinition {
  market_code: string;
  display_name: string;
  country_code: string;
  region_code: string;
  currency_code: string;
  language_codes: string[];
  supported_paths: string[];
  regulatory_summary: Record<string, unknown>;
}

export interface MarketOption extends MarketDefinition {
  code: string;
  state: string;
  label: string;
  zip: string;
  city: string;
  country_label: string;
}

export interface ScenarioVariant {
  label: string;
  item_sku: string;
  market_code: string;
  state?: string;
  zip?: string;
  county?: string | null;
  expected_outcome: string;
  sellers: Array<{ id: string; name: string }>;
  context?: EvaluationContext;
  seller_id?: string;
  timestamp?: string;
  customer_location?: Partial<CustomerLocation>;
  locale?: DiagnosisLocale;
  narration?: string;
  primary_node_id?: string;
  nearby_nodes?: string[];
}

export interface Scenario {
  id: number;
  label: string;
  short_label: string;
  what_it_proves: string;
  narration?: string;
  variants: ScenarioVariant[];
}

export interface CircuitBreakerState {
  service: string;
  state: "closed" | "open" | "half_open";
  failure_count: number;
  last_failure_at?: string | null;
  last_success_at?: string | null;
  opened_at?: string | null;
  fallback_mode: string;
  recent_events: Array<Record<string, unknown>>;
}

export interface CircuitBreakerResponse {
  breakers: CircuitBreakerState[];
}

export interface BlockedItemStat {
  item_id: string;
  item_name?: string;
  blocked_count: number;
  revenue_at_risk?: number;
  market_code?: string;
}

export interface RuleImpactStat {
  rule_name: string;
  block_count: number;
  gate_count?: number;
  warning_count?: number;
  reversal_rate?: number;
  market_code?: string;
}

export interface MarketCoverageStat {
  market_code: string;
  eligible_rate?: number;
  blocked_rate?: number;
  eligibility_rate?: number;
  low_confidence_rate?: number;
}

export interface BatchEvaluateRequest {
  requests: EvaluateRequest[];
}

export interface BatchEvaluateResponse {
  results: EligibilityResponse[];
  total_requests: number;
  succeeded: number;
  failed: number;
  total_ms: number;
  p50_ms: number;
  p95_ms: number;
  p99_ms: number;
}
