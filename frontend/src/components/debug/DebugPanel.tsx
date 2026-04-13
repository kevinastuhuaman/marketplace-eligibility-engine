import { useEvaluationStore } from "../../store/evaluation-store";
import { CircuitBreakerPanel } from "./CircuitBreakerPanel";
import { DiagnosisTracePanel } from "./DiagnosisTracePanel";
import { RulePipeline } from "./RulePipeline";
import { FulfillmentDiagram } from "./FulfillmentDiagram";
import { ConflictResolution } from "./ConflictResolution";
import { MetricsBar } from "./MetricsBar";

export function DebugPanel() {
  const response = useEvaluationStore((s) => s.response);
  const diagnosis = useEvaluationStore((s) => s.diagnosis);

  if (!response) {
    return (
      <div className="p-6 text-center">
        <div className="text-4xl mb-3">🔍</div>
        <p className="text-gray-400 text-sm">
          Evaluate an item to see the rule pipeline
        </p>
        <p className="text-gray-600 text-xs mt-1">
          Select a product and click "Check Eligibility"
        </p>
      </div>
    );
  }

  if (response.errors.length > 0) {
    return (
      <div className="p-6">
        <div className="bg-red-900/30 border border-red-800 rounded-lg p-4">
          <h3 className="text-sm font-bold text-red-400 mb-2">Evaluation Error</h3>
          {response.errors.map((e, i) => (
            <p key={i} className="text-xs text-red-300">{e}</p>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4 overflow-y-auto max-h-[calc(100vh-104px)]">
      <MetricsBar response={response} />

      {response.debug && <RulePipeline debug={response.debug} />}

      <FulfillmentDiagram paths={response.paths} />

      <ConflictResolution resolutions={response.conflict_resolutions} />

      <DiagnosisTracePanel diagnosis={diagnosis} />

      <CircuitBreakerPanel />
    </div>
  );
}
