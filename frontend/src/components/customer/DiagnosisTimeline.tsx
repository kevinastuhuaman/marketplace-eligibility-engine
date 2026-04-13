import type { DiagnosisResponse } from "../../types/api";

export function DiagnosisTimeline({
  diagnosis,
  isLoading,
}: {
  diagnosis: DiagnosisResponse | null;
  isLoading: boolean;
}) {
  if (!diagnosis && !isLoading) {
    return null;
  }

  return (
    <div className="rounded-xl border border-walmart-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-walmart-blue">
            Diagnosis
          </p>
          <h3 className="text-sm font-semibold text-walmart-gray-900">
            Root cause analysis
          </h3>
        </div>
        {isLoading && (
          <span className="text-xs text-walmart-gray-500">Analyzing...</span>
        )}
      </div>

      {diagnosis?.primary_finding && (
        <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-red-800">
            Primary Finding
          </p>
          <p className="mt-1 text-sm font-medium text-red-900">
            {diagnosis.primary_finding.localized_explanation}
          </p>
          <p className="mt-1 text-xs text-red-800">
            Suggested fix: {diagnosis.primary_finding.suggested_fix}
          </p>
        </div>
      )}

      {diagnosis?.findings?.length ? (
        <div className="mt-3 space-y-2">
          {diagnosis.findings.map((finding, index) => (
            <div
              key={`${finding.path_code}-${finding.cause_code}-${index}`}
              className="rounded-lg border border-walmart-gray-200 bg-walmart-gray-50 p-3"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-walmart-gray-500">
                  {finding.path_code}
                </p>
                <span className="text-[10px] font-semibold uppercase tracking-wide text-walmart-gray-500">
                  {finding.source_service}
                </span>
              </div>
              <p className="mt-1 text-sm text-walmart-gray-900">
                {finding.localized_explanation}
              </p>
              <p className="mt-1 text-xs text-walmart-gray-500">
                {finding.rule_name ?? finding.cause_code} · impacts about {finding.affected_items_estimate} item(s)
              </p>
            </div>
          ))}
        </div>
      ) : (
        !isLoading && (
          <p className="mt-3 text-sm text-walmart-gray-500">
            No additional diagnosis was needed for this evaluation.
          </p>
        )
      )}
    </div>
  );
}
