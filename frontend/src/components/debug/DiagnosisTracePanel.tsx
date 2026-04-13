import type { DiagnosisResponse } from "../../types/api";

export function DiagnosisTracePanel({
  diagnosis,
}: {
  diagnosis: DiagnosisResponse | null;
}) {
  if (!diagnosis?.trace?.length) {
    return null;
  }

  return (
    <div className="rounded-lg border border-debug-border bg-debug-surface p-4">
      <h3 className="text-sm font-semibold text-white">Diagnosis Trace</h3>
      <div className="mt-3 space-y-2">
        {diagnosis.trace.map((step) => (
          <div key={`${step.step}-${step.service}-${step.operation}`} className="rounded border border-slate-700 p-2">
            <div className="flex items-center justify-between text-xs text-slate-300">
              <span>
                {step.step}. {step.service}
              </span>
              <span>{step.duration_ms ?? 0}ms</span>
            </div>
            <p className="mt-1 text-xs text-white">{step.operation}</p>
            {step.state && (
              <p className="mt-1 text-[11px] text-slate-400">state: {step.state}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
