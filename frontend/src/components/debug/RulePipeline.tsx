import { useState } from "react";
import clsx from "clsx";
import type { DebugInfo } from "../../types/api";
import { RuleCard } from "./RuleCard";

export function RulePipeline({ debug }: { debug: DebugInfo }) {
  const [activeTab, setActiveTab] = useState(0);
  const [showUnmatched, setShowUnmatched] = useState(false);

  const pathEval = debug.per_path_evaluations[activeTab];
  if (!pathEval) return null;

  const matched = pathEval.rules.filter((r) => r.matched);
  const unmatched = pathEval.rules.filter((r) => !r.matched);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-white">Rule Pipeline</h3>
        <span className="text-xs text-gray-400">
          {debug.rules_loaded} loaded, {debug.rules_triggered} triggered, {debug.rules_suppressed} suppressed
        </span>
      </div>

      <div className="flex gap-1">
        {debug.per_path_evaluations.map((pe, i) => (
          <button
            key={pe.path_code}
            onClick={() => setActiveTab(i)}
            className={clsx(
              "px-3 py-1 rounded text-xs font-medium transition-colors",
              i === activeTab
                ? "bg-walmart-blue text-white"
                : "bg-debug-surface text-gray-400 hover:text-white"
            )}
          >
            {pe.path_code.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      <div className="space-y-1.5">
        {matched.map((rule) => (
          <RuleCard key={rule.rule_id} rule={rule} />
        ))}
      </div>

      {unmatched.length > 0 && (
        <div>
          <button
            onClick={() => setShowUnmatched(!showUnmatched)}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            {showUnmatched ? "▼" : "▶"} {unmatched.length} rules not matched
          </button>
          {showUnmatched && (
            <div className="space-y-1 mt-1.5">
              {unmatched.map((rule) => (
                <RuleCard key={rule.rule_id} rule={rule} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
