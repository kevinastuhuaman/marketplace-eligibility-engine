import clsx from "clsx";
import type { EligibilityResponse } from "../../types/api";

export function MetricsBar({ response }: { response: EligibilityResponse }) {
  const metrics = [
    { label: "Rules Loaded", value: response.rules_loaded },
    { label: "Triggered", value: response.rules_evaluated },
    { label: "Suppressed", value: response.rules_suppressed },
    {
      label: "Eval Time",
      value: `${response.evaluation_ms}ms`,
      color:
        response.evaluation_ms < 20
          ? "text-green-400"
          : response.evaluation_ms < 50
            ? "text-yellow-400"
            : "text-red-400",
    },
  ];

  return (
    <div className="grid grid-cols-4 gap-2">
      {metrics.map((m) => (
        <div
          key={m.label}
          className="bg-debug-surface border border-debug-border rounded-lg p-2 text-center"
        >
          <p className="text-[10px] text-gray-500 uppercase tracking-wide">{m.label}</p>
          <p className={clsx("text-lg font-bold", m.color ?? "text-white")}>
            {m.value}
          </p>
        </div>
      ))}
    </div>
  );
}
