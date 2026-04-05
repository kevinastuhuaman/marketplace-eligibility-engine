"""Unit tests for the rule evaluation engine.

No database, no Docker, no network -- pure function tests only.
"""

import sys
import os
from types import SimpleNamespace

import pytest

# Ensure the eligibility-service package is importable
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "services",
        "eligibility-service",
    ),
)

from app.engine.evaluator import (
    evaluate_condition,
    evaluate_conditions,
    evaluate_rules,
    resolve_and_accumulate,
    resolve_requirements,
    determine_path_status,
    RuleResult,
    TriggeredRule,
)


# ---------------------------------------------------------------------------
# Helper: create a mock rule object with the attributes evaluate_rules expects
# ---------------------------------------------------------------------------

def make_rule(
    rule_id: int = 1,
    rule_name: str = "test-rule",
    rule_type: str = "item",
    action: str = "BLOCK",
    priority: int = 10,
    conflict_group: str | None = None,
    reason: str = "test reason",
    blocked_paths: list[str] | None = None,
    rule_definition: dict | None = None,
    metadata_: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        rule_id=rule_id,
        rule_name=rule_name,
        rule_type=rule_type,
        action=action,
        priority=priority,
        conflict_group=conflict_group,
        reason=reason,
        blocked_paths=blocked_paths or ["WFS"],
        rule_definition=rule_definition or {"conditions": {}},
        metadata_=metadata_,
    )


# ===================================================================
# Condition evaluation tests
# ===================================================================


class TestEvaluateCondition:
    def test_equal_to_string(self):
        cond = {"name": "market_state", "operator": "equal_to", "value": "UT"}
        assert evaluate_condition(cond, {"market_state": "UT"}) is True

    def test_equal_to_string_mismatch(self):
        cond = {"name": "market_state", "operator": "equal_to", "value": "UT"}
        assert evaluate_condition(cond, {"market_state": "CO"}) is False

    def test_contains_in_list(self):
        cond = {"name": "compliance_tags", "operator": "contains", "value": "alcohol"}
        variables = {"compliance_tags": ["alcohol", "age_restricted"]}
        assert evaluate_condition(cond, variables) is True

    def test_contains_not_in_list(self):
        cond = {"name": "compliance_tags", "operator": "contains", "value": "hazmat"}
        variables = {"compliance_tags": ["alcohol"]}
        assert evaluate_condition(cond, variables) is False

    def test_greater_than(self):
        cond = {"name": "seller_defect_rate", "operator": "greater_than", "value": 0.03}
        assert evaluate_condition(cond, {"seller_defect_rate": 0.08}) is True

    def test_greater_than_below(self):
        cond = {"name": "seller_defect_rate", "operator": "greater_than", "value": 0.03}
        assert evaluate_condition(cond, {"seller_defect_rate": 0.02}) is False

    def test_less_than(self):
        cond = {"name": "request_hour", "operator": "less_than", "value": 10}
        assert evaluate_condition(cond, {"request_hour": 8}) is True

    def test_in_list(self):
        cond = {"name": "seller_trust_tier", "operator": "in", "value": ["new", "standard"]}
        assert evaluate_condition(cond, {"seller_trust_tier": "new"}) is True

    def test_not_in_list(self):
        cond = {"name": "request_month", "operator": "not_in", "value": [6, 7]}
        assert evaluate_condition(cond, {"request_month": 10}) is True

    def test_between(self):
        cond = {"name": "request_month", "operator": "between", "value": [6, 7]}
        assert evaluate_condition(cond, {"request_month": 6}) is True

    def test_null_variable_returns_false(self):
        cond = {"name": "customer_age", "operator": "greater_than", "value": 21}
        assert evaluate_condition(cond, {"customer_age": None}) is False


# ===================================================================
# Nested condition tests
# ===================================================================


class TestEvaluateConditions:
    def test_all_conditions_pass(self):
        conditions = {
            "all": [
                {"name": "market_state", "operator": "equal_to", "value": "UT"},
                {"name": "request_month", "operator": "less_than", "value": 12},
            ]
        }
        variables = {"market_state": "UT", "request_month": 6}
        assert evaluate_conditions(conditions, variables) is True

    def test_all_conditions_one_fails(self):
        conditions = {
            "all": [
                {"name": "market_state", "operator": "equal_to", "value": "UT"},
                {"name": "request_month", "operator": "less_than", "value": 5},
            ]
        }
        variables = {"market_state": "UT", "request_month": 6}
        assert evaluate_conditions(conditions, variables) is False

    def test_any_conditions_one_passes(self):
        conditions = {
            "any": [
                {"name": "market_state", "operator": "equal_to", "value": "CA"},
                {"name": "market_state", "operator": "equal_to", "value": "UT"},
            ]
        }
        variables = {"market_state": "UT"}
        assert evaluate_conditions(conditions, variables) is True

    def test_nested_all_any(self):
        conditions = {
            "all": [
                {"name": "market_state", "operator": "equal_to", "value": "UT"},
                {
                    "any": [
                        {"name": "request_month", "operator": "equal_to", "value": 12},
                        {"name": "request_month", "operator": "equal_to", "value": 6},
                    ]
                },
            ]
        }
        variables = {"market_state": "UT", "request_month": 6}
        assert evaluate_conditions(conditions, variables) is True


# ===================================================================
# Rule evaluation tests
# ===================================================================


class TestEvaluateRules:
    def test_rule_triggers(self):
        rule = make_rule(
            rule_id=1,
            rule_name="utah-alcohol",
            rule_definition={
                "conditions": {
                    "all": [
                        {"name": "market_state", "operator": "equal_to", "value": "UT"},
                    ]
                }
            },
        )
        variables = {"market_state": "UT"}
        triggered = evaluate_rules([rule], variables)
        assert len(triggered) == 1
        assert triggered[0].rule_id == 1

    def test_rule_does_not_trigger(self):
        rule = make_rule(
            rule_id=1,
            rule_name="utah-alcohol",
            rule_definition={
                "conditions": {
                    "all": [
                        {"name": "market_state", "operator": "equal_to", "value": "UT"},
                    ]
                }
            },
        )
        variables = {"market_state": "CO"}
        triggered = evaluate_rules([rule], variables)
        assert len(triggered) == 0

    def test_multiple_rules_some_trigger(self):
        rule1 = make_rule(
            rule_id=1,
            rule_name="utah-alcohol",
            rule_definition={
                "conditions": {"all": [{"name": "market_state", "operator": "equal_to", "value": "UT"}]}
            },
        )
        rule2 = make_rule(
            rule_id=2,
            rule_name="high-defect",
            rule_definition={
                "conditions": {"all": [{"name": "seller_defect_rate", "operator": "greater_than", "value": 0.05}]}
            },
        )
        rule3 = make_rule(
            rule_id=3,
            rule_name="california-only",
            rule_definition={
                "conditions": {"all": [{"name": "market_state", "operator": "equal_to", "value": "CA"}]}
            },
        )
        variables = {"market_state": "UT", "seller_defect_rate": 0.08}
        triggered = evaluate_rules([rule1, rule2, rule3], variables)
        assert len(triggered) == 2
        triggered_ids = {t.rule_id for t in triggered}
        assert triggered_ids == {1, 2}


# ===================================================================
# Conflict resolution tests
# ===================================================================


class TestResolveAndAccumulate:
    def test_no_conflict_group_all_accumulate(self):
        t1 = TriggeredRule(
            rule_id=1, rule_name="rule-a", rule_type="item", action="BLOCK",
            priority=10, conflict_group=None, reason="reason a",
            blocked_paths=["WFS"], rule_definition={}, metadata={},
        )
        t2 = TriggeredRule(
            rule_id=2, rule_name="rule-b", rule_type="seller", action="WARN",
            priority=20, conflict_group=None, reason="reason b",
            blocked_paths=["WFS"], rule_definition={}, metadata={},
        )
        result = resolve_and_accumulate([t1, t2])
        # Both should survive -- no conflict groups
        assert result.rules_suppressed == 0
        assert "WFS" in result.violations  # BLOCK rule
        assert len(result.warnings) == 1  # WARN rule

    def test_conflict_group_narrower_scope_wins(self):
        # geographic scope = 20, seller scope = 40 -> seller wins
        geo_rule = TriggeredRule(
            rule_id=1, rule_name="geo-rule", rule_type="geographic", action="WARN",
            priority=10, conflict_group="alcohol-group", reason="geo reason",
            blocked_paths=["WFS"], rule_definition={}, metadata={},
        )
        seller_rule = TriggeredRule(
            rule_id=2, rule_name="seller-rule", rule_type="seller", action="WARN",
            priority=10, conflict_group="alcohol-group", reason="seller reason",
            blocked_paths=["WFS"], rule_definition={}, metadata={},
        )
        result = resolve_and_accumulate([geo_rule, seller_rule])
        # Seller (scope 40) beats geographic (scope 20)
        assert result.rules_suppressed == 1
        assert len(result.warnings) == 1
        assert result.warnings[0]["rule_name"] == "seller-rule"

    def test_block_never_suppressed_by_warn(self):
        # Broader rule is BLOCK, narrower is WARN.
        # The BLOCK should survive because it is more restrictive.
        geo_block = TriggeredRule(
            rule_id=1, rule_name="geo-block", rule_type="geographic", action="BLOCK",
            priority=10, conflict_group="safety-group", reason="geo blocks",
            blocked_paths=["WFS"], rule_definition={}, metadata={},
        )
        seller_warn = TriggeredRule(
            rule_id=2, rule_name="seller-warn", rule_type="seller", action="WARN",
            priority=10, conflict_group="safety-group", reason="seller warns",
            blocked_paths=["WFS"], rule_definition={}, metadata={},
        )
        result = resolve_and_accumulate([geo_block, seller_warn])
        # Seller wins by scope, but geo_block has higher ACTION_RANK (BLOCK > WARN)
        # so geo_block also survives as a safety property
        assert "WFS" in result.violations  # BLOCK survived
        assert result.violations["WFS"][0]["rule_name"] == "geo-block"

    def test_same_scope_lower_priority_wins(self):
        rule_p10 = TriggeredRule(
            rule_id=1, rule_name="rule-p10", rule_type="item", action="WARN",
            priority=10, conflict_group="dup-group", reason="p10",
            blocked_paths=["WFS"], rule_definition={}, metadata={},
        )
        rule_p50 = TriggeredRule(
            rule_id=2, rule_name="rule-p50", rule_type="item", action="WARN",
            priority=50, conflict_group="dup-group", reason="p50",
            blocked_paths=["WFS"], rule_definition={}, metadata={},
        )
        result = resolve_and_accumulate([rule_p10, rule_p50])
        # Same scope (item=50), so sorted by priority: 10 < 50 -> p10 wins
        assert result.rules_suppressed == 1
        assert len(result.warnings) == 1
        assert result.warnings[0]["rule_name"] == "rule-p10"


# ===================================================================
# REQUIRE resolution tests
# ===================================================================


class TestResolveRequirements:
    def _make_require_result(self, variable_name, operator, threshold, path="WFS"):
        """Helper to build a RuleResult containing a single REQUIRE."""
        req = {
            "rule_id": 100,
            "rule_name": "age-verification",
            "action": "REQUIRE",
            "reason": "Customer age verification required",
            "priority": 10,
            "satisfied": False,
            "requirement_type": "age_verification",
            "parameters": {
                "variable": variable_name,
                "operator": operator,
                "value": threshold,
            },
            "metadata": {},
        }
        return RuleResult(
            violations={},
            requirements={path: [req]},
            gates={},
            warnings=[],
            conflict_resolutions=[],
            rules_evaluated=1,
            rules_suppressed=0,
        )

    def test_require_not_provided_stays_conditional(self):
        result = self._make_require_result("customer_age", "greater_than_or_equal_to", 21)
        variables = {"customer_age": None}
        resolved = resolve_requirements(result, variables)
        # Variable is None, so requirement stays unsatisfied
        assert resolved.requirements["WFS"][0]["satisfied"] is False
        assert "WFS" not in resolved.violations

    def test_require_provided_and_passes(self):
        result = self._make_require_result("customer_age", "greater_than_or_equal_to", 21)
        variables = {"customer_age": 25}
        resolved = resolve_requirements(result, variables)
        assert resolved.requirements["WFS"][0]["satisfied"] is True

    def test_require_provided_and_fails_escalates_to_block(self):
        result = self._make_require_result("customer_age", "greater_than_or_equal_to", 21)
        variables = {"customer_age": 17}
        resolved = resolve_requirements(result, variables)
        # Should have escalated to a BLOCK violation
        assert "WFS" in resolved.violations
        assert resolved.violations["WFS"][0]["action"] == "BLOCK"
        assert "escalated" in resolved.violations["WFS"][0]["reason"].lower()


# ===================================================================
# Path status tests
# ===================================================================


class TestDeterminePathStatus:
    def test_blocked_path(self):
        result = RuleResult(
            violations={"WFS": [{"rule_id": 1, "action": "BLOCK", "reason": "blocked"}]},
            requirements={},
            gates={},
            warnings=[],
            conflict_resolutions=[],
            rules_evaluated=1,
            rules_suppressed=0,
        )
        status, eligible = determine_path_status("WFS", result)
        assert status == "blocked"
        assert eligible is False

    def test_gated_path(self):
        result = RuleResult(
            violations={},
            requirements={},
            gates={"WFS": [{"rule_id": 2, "gate_type": "metric_threshold", "resolved": False}]},
            warnings=[],
            conflict_resolutions=[],
            rules_evaluated=1,
            rules_suppressed=0,
        )
        status, eligible = determine_path_status("WFS", result)
        assert status == "gated"
        assert eligible is False

    def test_conditional_path(self):
        result = RuleResult(
            violations={},
            requirements={"WFS": [{"rule_id": 3, "satisfied": False}]},
            gates={},
            warnings=[],
            conflict_resolutions=[],
            rules_evaluated=1,
            rules_suppressed=0,
        )
        status, eligible = determine_path_status("WFS", result)
        assert status == "conditional"
        assert eligible is True

    def test_clear_path(self):
        result = RuleResult(
            violations={},
            requirements={},
            gates={},
            warnings=[],
            conflict_resolutions=[],
            rules_evaluated=0,
            rules_suppressed=0,
        )
        status, eligible = determine_path_status("WFS", result)
        assert status == "clear"
        assert eligible is True
