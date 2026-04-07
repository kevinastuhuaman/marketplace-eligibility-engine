import { useState } from "react";
import clsx from "clsx";
import type { DebugRule } from "../../types/api";
import { ActionBadge } from "../shared/ActionBadge";

const BORDER_COLORS: Record<string, string> = {
  BLOCK: "border-l-red-600",
  GATE: "border-l-orange-500",
  REQUIRE: "border-l-yellow-500",
  WARN: "border-l-blue-500",
};

export function RuleCard({ rule }: { rule: DebugRule }) {
  const [expanded, setExpanded] = useState(false);

  if (!rule.matched) {
    return (
      <div className="px-3 py-2 bg-debug-surface/50 rounded border border-debug-border/30 opacity-40">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-mono">#{rule.rule_id}</span>
          <span className="text-xs text-gray-500">{rule.rule_name}</span>
          <span className="text-[10px] text-gray-600 ml-auto">not matched</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={clsx(
        "rounded border-l-4 bg-debug-surface border border-debug-border cursor-pointer transition-colors hover:bg-debug-surface/80",
        rule.suppressed ? "border-l-gray-500 opacity-60" : BORDER_COLORS[rule.action]
      )}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="px-3 py-2">
        <div className="flex items-center gap-2">
          <ActionBadge action={rule.action} />
          <span className={clsx("text-sm font-medium", rule.suppressed && "line-through text-gray-400")}>
            {rule.rule_name}
          </span>
          <span className="text-[10px] text-gray-500 bg-debug-bg px-1.5 py-0.5 rounded">
            {rule.rule_type}
          </span>
          <span className="ml-auto text-[10px] text-gray-500">
            {rule.survived && "survived"}
            {rule.suppressed && "suppressed"}
          </span>
        </div>
        <p className={clsx("text-xs mt-1", rule.suppressed ? "text-gray-500" : "text-gray-300")}>
          {rule.reason}
        </p>
        {rule.suppressed && rule.suppressed_by && (
          <p className="text-xs text-orange-400 mt-1">
            Suppressed by higher-precedence rule in conflict group: {rule.suppressed_by.rule_name}
          </p>
        )}
        {rule.blocked_paths.length > 0 && (
          <div className="flex gap-1 mt-1">
            {rule.blocked_paths.map((p) => (
              <span key={p} className="text-[10px] px-1.5 py-0.5 rounded bg-red-900/30 text-red-300">
                {p}
              </span>
            ))}
          </div>
        )}
      </div>
      {expanded && (
        <div className="px-3 py-2 border-t border-debug-border bg-debug-bg/50">
          <p className="text-[10px] text-gray-500 mb-1 font-mono">rule_definition</p>
          <pre className="text-[10px] text-gray-400 overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(rule.rule_definition, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
