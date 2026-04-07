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

export interface EvaluateRequest {
  item_id: string;
  market_code: string;
  customer_location: { state: string; zip: string };
  seller_id?: string | null;
  timestamp: string;
  context?: {
    customer_age?: number;
    requested_quantity?: number;
  };
}

export interface Violation {
  rule_id: number;
  rule_name: string;
  action: string;
  reason: string;
  priority: number;
  metadata: Record<string, unknown>;
}

export interface Requirement {
  rule_id: number;
  rule_name: string;
  action: string;
  reason: string;
  priority: number;
  satisfied: boolean;
  requirement_type: string;
  parameters: Record<string, unknown>;
  metadata: Record<string, unknown>;
}

export interface Gate {
  rule_id: number;
  rule_name: string;
  action: string;
  reason: string;
  priority: number;
  gate_type: string;
  current: Record<string, unknown>;
  required: Record<string, unknown>;
  gap: Record<string, unknown>;
  metadata: Record<string, unknown>;
}

export interface Warning {
  rule_id: number;
  rule_name: string;
  action: string;
  reason: string;
  priority: number;
  metadata: Record<string, unknown>;
}

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
  status: "blocked" | "gated" | "conditional" | "clear";
  violations: Violation[];
  requirements: Requirement[];
  gates: Gate[];
  inventory_available: number | null;
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
  debug: DebugInfo | null;
}

export interface SellerInfo {
  seller_id: string;
  name: string;
  trust_tier: string;
  defect_rate: number;
}

export interface ScenarioVariant {
  label: string;
  item_sku: string;
  market_code: string;
  state: string;
  zip: string;
  expected_outcome: string;
  sellers: Array<{ id: string; name: string }>;
  context?: {
    customer_age?: number;
    requested_quantity?: number;
  };
  seller_id?: string;
  timestamp?: string;
}

export interface Scenario {
  id: number;
  label: string;
  short_label: string;
  what_it_proves: string;
  variants: ScenarioVariant[];
}
