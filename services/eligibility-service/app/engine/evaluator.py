"""Rule evaluation engine with 4 action types and conflict resolution."""
from collections import defaultdict
from dataclasses import dataclass, field


ACTION_RANK = {"BLOCK": 4, "GATE": 3, "REQUIRE": 2, "WARN": 1}

SCOPE_SCORE = {
    "item": 50,
    "seller": 40,
    "regulation": 35,
    "category": 30,
    "geographic": 20,
    "geo_zone": 20,
    "temporal": 10,
    "quantity": 15,
    "availability": 12,
}


@dataclass
class TriggeredRule:
    rule_id: int
    rule_name: str
    rule_type: str
    action: str
    priority: int
    conflict_group: str | None
    reason: str
    blocked_paths: list[str]
    rule_definition: dict
    metadata: dict = field(default_factory=dict)


@dataclass
class RuleResult:
    violations: dict  # path_code -> list of violation dicts
    requirements: dict  # path_code -> list of requirement dicts
    gates: dict  # path_code -> list of gate dicts
    warnings: list  # list of warning dicts
    conflict_resolutions: list
    rules_evaluated: int
    rules_suppressed: int


def evaluate_condition(condition: dict, variables: dict) -> bool:
    """Evaluate a single condition against variables."""
    name = condition.get("name", "")
    operator = condition.get("operator", "")
    value = condition.get("value")

    var_value = variables.get(name)
    if var_value is None and operator not in {"outside_zone"}:
        return False  # Variable not available, condition doesn't match

    if operator == "equal_to":
        return var_value == value
    elif operator == "not_equal_to":
        return var_value != value
    elif operator == "greater_than":
        try:
            return float(var_value) > float(value)
        except (ValueError, TypeError):
            return False
    elif operator == "greater_than_or_equal_to":
        try:
            return float(var_value) >= float(value)
        except (ValueError, TypeError):
            return False
    elif operator == "less_than":
        try:
            return float(var_value) < float(value)
        except (ValueError, TypeError):
            return False
    elif operator == "less_than_or_equal_to":
        try:
            return float(var_value) <= float(value)
        except (ValueError, TypeError):
            return False
    elif operator == "contains":
        if isinstance(var_value, list):
            return value in var_value
        return value in str(var_value)
    elif operator == "does_not_contain":
        if isinstance(var_value, list):
            return value not in var_value
        return value not in str(var_value)
    elif operator == "in":
        try:
            return var_value in value
        except TypeError:
            return False
    elif operator == "not_in":
        try:
            return var_value not in value
        except TypeError:
            return False
    elif operator == "between":
        try:
            return value[0] <= float(var_value) <= value[1]
        except (ValueError, TypeError, IndexError):
            return False
    elif operator == "within_zone":
        if isinstance(var_value, list):
            if isinstance(value, list):
                return any(zone in var_value for zone in value)
            return value in var_value
        if isinstance(var_value, bool):
            return bool(var_value)
        return False
    elif operator == "outside_zone":
        if isinstance(var_value, list):
            if isinstance(value, list):
                return all(zone not in var_value for zone in value)
            return value not in var_value
        if isinstance(var_value, bool):
            return not var_value
        return True
    return False


def evaluate_conditions(conditions: dict, variables: dict) -> bool:
    """Evaluate nested all/any conditions."""
    if "all" in conditions:
        return all(
            evaluate_conditions(c, variables)
            if ("all" in c or "any" in c)
            else evaluate_condition(c, variables)
            for c in conditions["all"]
        )
    elif "any" in conditions:
        return any(
            evaluate_conditions(c, variables)
            if ("all" in c or "any" in c)
            else evaluate_condition(c, variables)
            for c in conditions["any"]
        )
    else:
        return evaluate_condition(conditions, variables)


def evaluate_rules(rules: list, variables: dict) -> list[TriggeredRule]:
    """Evaluate all rules against variables, return triggered rules."""
    triggered = []
    for rule in rules:
        conditions = rule.rule_definition.get("conditions", {})
        if evaluate_conditions(conditions, variables):
            triggered.append(
                TriggeredRule(
                    rule_id=rule.rule_id,
                    rule_name=rule.rule_name,
                    rule_type=rule.rule_type,
                    action=rule.action,
                    priority=rule.priority,
                    conflict_group=rule.conflict_group,
                    reason=rule.reason,
                    blocked_paths=rule.blocked_paths or [],
                    rule_definition=rule.rule_definition,
                    metadata=rule.metadata_ or {},
                )
            )
    return triggered


def resolve_and_accumulate(triggered: list[TriggeredRule]) -> RuleResult:
    """Two-phase: resolve conflict groups, then accumulate survivors."""
    grouped = defaultdict(list)
    ungrouped = []

    for rule in triggered:
        if rule.conflict_group:
            grouped[rule.conflict_group].append(rule)
        else:
            ungrouped.append(rule)

    survivors = list(ungrouped)
    suppressed = []
    conflict_resolutions = []

    for group_name, group_rules in grouped.items():
        sorted_group = sorted(
            group_rules,
            key=lambda r: (-SCOPE_SCORE.get(r.rule_type, 0), r.priority, r.rule_id),
        )
        winner = sorted_group[0]
        survivors.append(winner)

        for loser in sorted_group[1:]:
            if ACTION_RANK.get(loser.action, 0) > ACTION_RANK.get(winner.action, 0):
                survivors.append(loser)  # More restrictive, keep it
            else:
                suppressed.append(loser)
                conflict_resolutions.append(
                    {
                        "winner_rule_id": winner.rule_id,
                        "winner_rule_name": winner.rule_name,
                        "suppressed_rule_id": loser.rule_id,
                        "suppressed_rule_name": loser.rule_name,
                        "reason": f"{winner.rule_type} {winner.action} (priority {winner.priority}) suppresses {loser.rule_type} {loser.action} (priority {loser.priority}) in group '{group_name}'",
                    }
                )

    # Accumulate survivors
    sorted_survivors = sorted(survivors, key=lambda r: (r.priority, r.rule_id))

    violations = defaultdict(list)
    requirements = defaultdict(list)
    gates = defaultdict(list)
    warnings = []

    for rule in sorted_survivors:
        if rule.action == "BLOCK":
            v = {
                "rule_id": rule.rule_id,
                "rule_name": rule.rule_name,
                "action": "BLOCK",
                "reason": rule.reason,
                "priority": rule.priority,
                "metadata": rule.metadata,
            }
            for path in rule.blocked_paths or ["__all__"]:
                violations[path].append(v)
        elif rule.action == "WARN":
            warnings.append(
                {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.rule_name,
                    "action": "WARN",
                    "reason": rule.reason,
                    "priority": rule.priority,
                    "metadata": rule.metadata,
                }
            )
        elif rule.action == "REQUIRE":
            req_spec = rule.rule_definition.get("requirement", {})
            for path in rule.blocked_paths or ["__all__"]:
                requirements[path].append({
                    "rule_id": rule.rule_id,
                    "rule_name": rule.rule_name,
                    "action": "REQUIRE",
                    "reason": rule.reason,
                    "priority": rule.priority,
                    "satisfied": False,
                    "requirement_type": req_spec.get("type", "unknown"),
                    "parameters": dict(req_spec),
                    "metadata": dict(rule.metadata) if rule.metadata else {},
                })
        elif rule.action == "GATE":
            gate_spec = rule.rule_definition.get("gate", {})
            for path in rule.blocked_paths or ["__all__"]:
                gates[path].append({
                    "rule_id": rule.rule_id,
                    "rule_name": rule.rule_name,
                    "action": "GATE",
                    "reason": rule.reason,
                    "priority": rule.priority,
                    "gate_type": gate_spec.get("type", "metric_threshold"),
                    "current": {},
                    "required": dict(gate_spec.get("thresholds", {})),
                    "gap": {},
                    "metadata": dict(rule.metadata) if rule.metadata else {},
                })

    return RuleResult(
        violations=dict(violations),
        requirements=dict(requirements),
        gates=dict(gates),
        warnings=warnings,
        conflict_resolutions=conflict_resolutions,
        rules_evaluated=len(triggered),
        rules_suppressed=len(suppressed),
    )


def resolve_requirements(result: RuleResult, variables: dict) -> RuleResult:
    """Resolve REQUIRE rules against provided context variables.
    If context satisfies the requirement -> mark satisfied.
    If context fails the requirement -> escalate to BLOCK."""
    for path, reqs in list(result.requirements.items()):
        for req in reqs:
            params = req.get("parameters", {})
            var_name = params.get("variable")
            if var_name and variables.get(var_name) is not None:
                op = params.get("operator", "greater_than_or_equal_to")
                threshold = params.get("value")
                actual = variables.get(var_name)

                passed = False
                try:
                    if op == "greater_than":
                        passed = float(actual) > float(threshold)
                    elif op == "greater_than_or_equal_to":
                        passed = float(actual) >= float(threshold)
                    elif op == "equal_to":
                        passed = actual == threshold
                    elif op == "less_than":
                        passed = float(actual) < float(threshold)
                    elif op == "less_than_or_equal_to":
                        passed = float(actual) <= float(threshold)
                except (ValueError, TypeError):
                    passed = False

                if passed:
                    req["satisfied"] = True
                    req["reason"] = f"{req['reason']} (verified: {var_name}={actual})"
                else:
                    # Escalate to BLOCK
                    violation = {
                        "rule_id": req["rule_id"],
                        "rule_name": req["rule_name"],
                        "action": "BLOCK",
                        "reason": f"REQUIRE escalated to BLOCK: {var_name}={actual} does not meet threshold {threshold}",
                        "priority": req["priority"],
                        "metadata": req.get("metadata", {}),
                    }
                    if path not in result.violations:
                        result.violations[path] = []
                    result.violations[path].append(violation)
    return result


def determine_path_status(path_code: str, result: RuleResult) -> tuple[str, bool]:
    """Determine path status and eligibility."""
    path_violations = result.violations.get(path_code, []) + result.violations.get("__all__", [])
    if path_violations:
        return "blocked", False

    path_gates = result.gates.get(path_code, []) + result.gates.get("__all__", [])
    unresolved_gates = [g for g in path_gates if not g.get("resolved")]
    if unresolved_gates:
        return "gated", False

    path_reqs = result.requirements.get(path_code, []) + result.requirements.get(
        "__all__", []
    )
    unresolved_reqs = [r for r in path_reqs if not r.get("satisfied")]
    if unresolved_reqs:
        return "conditional", True

    return "clear", True
