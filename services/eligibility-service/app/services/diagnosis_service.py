from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import EligibilityAuditLog
from app.services.trace_context import get_trace
from shared.contracts.eligibility import DiagnosisResponse

PACIFIC = ZoneInfo("America/Los_Angeles")


def _localized_text(metadata: dict, market_code: str, fallback: str) -> str:
    diagnosis = metadata.get("diagnosis", {}) if isinstance(metadata, dict) else {}
    if market_code.startswith(("MX-", "CL-", "CR-")):
        return diagnosis.get("es") or diagnosis.get("en") or fallback
    return diagnosis.get("en") or fallback


def derive_primary_cause(response: dict) -> tuple[str | None, str | None]:
    for path in response.get("paths", []):
        if path.get("violations"):
            violation = path["violations"][0]
            metadata = violation.get("metadata", {})
            return metadata.get("source_service", "eligibility-service"), metadata.get(
                "cause_code", violation.get("rule_name")
            )
        if path.get("gates"):
            gate = path["gates"][0]
            metadata = gate.get("metadata", {})
            return metadata.get("source_service", "seller-service"), metadata.get(
                "cause_code", gate.get("rule_name")
            )
    return None, None


async def _affected_items_estimate(
    db: AsyncSession,
    cause_code: str | None,
    rule_name: str | None,
) -> int:
    if cause_code:
        result = await db.execute(
            select(func.count(func.distinct(EligibilityAuditLog.item_id))).where(
                EligibilityAuditLog.diagnosis_root_cause_code == cause_code
            )
        )
        count = result.scalar() or 0
        if count:
            return count
    if rule_name:
        result = await db.execute(
            select(EligibilityAuditLog).where(
                EligibilityAuditLog.blocking_rule_names.any(rule_name)
            )
        )
        audits = result.scalars().all()
        return len({str(audit.item_id) for audit in audits}) or 1
    return 1


async def build_diagnosis(
    db: AsyncSession,
    request_data: dict,
    evaluation: dict,
    locale: str = "auto",
) -> dict:
    findings = []
    suggested_fixes = []
    market_code = request_data["market_code"]
    if locale == "en":
        market_code = "US-EN"
    elif locale == "es":
        market_code = "MX-CDMX"

    for path in evaluation.get("paths", []):
        for severity, key in (("block", "violations"), ("gate", "gates")):
            for entry in path.get(key, []):
                metadata = entry.get("metadata", {})
                cause_code = metadata.get("cause_code", entry.get("rule_name", "unknown_cause"))
                explanation = metadata.get("explanation") or entry.get("reason", "")
                localized_explanation = _localized_text(metadata, market_code, explanation)
                suggested_fix = metadata.get("suggested_fix", "Adjust the underlying source data or rule configuration.")
                affected_items_estimate = await _affected_items_estimate(
                    db,
                    cause_code,
                    entry.get("rule_name"),
                )
                finding = {
                    "path_code": path["path_code"],
                    "source_service": metadata.get("source_service", "eligibility-service"),
                    "source_entity": metadata.get("source_entity", "compliance_rule"),
                    "source_field": metadata.get("source_field", "rule_definition"),
                    "rule_id": entry.get("rule_id"),
                    "rule_name": entry.get("rule_name"),
                    "cause_code": cause_code,
                    "root_cause": explanation,
                    "explanation": explanation,
                    "localized_explanation": localized_explanation,
                    "suggested_fix": suggested_fix,
                    "affected_items_estimate": affected_items_estimate,
                    "severity": severity,
                }
                findings.append(finding)
                if suggested_fix not in suggested_fixes:
                    suggested_fixes.append(suggested_fix)

    if not findings and evaluation.get("warnings"):
        warning = evaluation["warnings"][0]
        findings.append(
            {
                "path_code": "__all__",
                "source_service": "eligibility-service",
                "source_entity": "warning",
                "source_field": "reason",
                "rule_id": warning.get("rule_id"),
                "rule_name": warning.get("rule_name"),
                "cause_code": warning.get("metadata", {}).get("cause_code", warning.get("rule_name")),
                "root_cause": warning.get("reason", ""),
                "explanation": warning.get("reason", ""),
                "localized_explanation": _localized_text(
                    warning.get("metadata", {}), market_code, warning.get("reason", "")
                ),
                "suggested_fix": warning.get("metadata", {}).get(
                    "suggested_fix", "Review the advisory details before checkout."
                ),
                "affected_items_estimate": 1,
                "severity": "warning",
            }
        )

    errors = evaluation.get("errors", [])
    overall_status = "error" if errors else "clear"
    if any(path["status"] == "blocked" for path in evaluation.get("paths", [])):
        overall_status = "blocked"
    elif any(path["status"] == "gated" for path in evaluation.get("paths", [])):
        overall_status = "gated"
    elif any(path["status"] == "low_confidence" for path in evaluation.get("paths", [])):
        overall_status = "low_confidence"
    elif any(path["status"] == "conditional" for path in evaluation.get("paths", [])):
        overall_status = "conditional"

    findings.sort(key=lambda finding: (0 if finding["severity"] == "block" else 1, finding["path_code"]))
    primary_finding = findings[0] if findings else None
    affected_items_estimate = max(
        (finding["affected_items_estimate"] for finding in findings),
        default=1,
    )

    diagnosis = DiagnosisResponse(
        evaluation=evaluation,
        overall_status=overall_status,
        primary_finding=primary_finding,
        findings=findings,
        suggested_fixes=suggested_fixes,
        affected_items_estimate=affected_items_estimate,
        trace=get_trace(),
        generated_at=datetime.now(PACIFIC),
    )
    return diagnosis.model_dump(mode="json")
