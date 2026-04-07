import type { ReactNode } from "react";
import { useEvaluationStore } from "../../store/evaluation-store";
import { DebugPanel } from "../debug/DebugPanel";

export function SplitPanel({ children }: { children: ReactNode }) {
  const testerMode = useEvaluationStore((s) => s.testerMode);

  return (
    <div className="flex min-h-[calc(100vh-56px-48px)]">
      <div
        className="transition-all duration-500 ease-in-out overflow-auto"
        style={{ width: testerMode ? "40%" : "100%" }}
      >
        {children}
      </div>
      <div
        className="transition-all duration-500 ease-in-out overflow-hidden bg-debug-bg text-white"
        style={{
          width: testerMode ? "60%" : "0%",
          opacity: testerMode ? 1 : 0,
        }}
      >
        {testerMode && <DebugPanel />}
      </div>
    </div>
  );
}
