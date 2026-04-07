import type { ConflictResolution as CR } from "../../types/api";

export function ConflictResolution({ resolutions }: { resolutions: CR[] }) {
  if (resolutions.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-bold text-white">Conflict Resolution</h3>
      <div className="space-y-2">
        {resolutions.map((cr, i) => (
          <div
            key={i}
            className="bg-debug-surface border border-debug-border rounded-lg p-3 flex items-center gap-3"
          >
            <div className="flex-1 text-right">
              <p className="text-xs text-gray-400 line-through">{cr.suppressed_rule_name}</p>
              <p className="text-[10px] text-gray-500">#{cr.suppressed_rule_id}</p>
            </div>
            <div className="flex-shrink-0 px-2 py-1 bg-orange-900/30 rounded text-[10px] text-orange-300 font-medium">
              SUPPRESSED BY
            </div>
            <div className="flex-1">
              <p className="text-xs text-green-400 font-medium">{cr.winner_rule_name}</p>
              <p className="text-[10px] text-gray-500">#{cr.winner_rule_id}</p>
            </div>
          </div>
        ))}
      </div>
      <p className="text-[10px] text-gray-600">
        Scope precedence: item(50) &gt; seller(40) &gt; category(30) &gt; geographic(20) &gt; quantity(15) &gt; temporal(10)
      </p>
    </div>
  );
}
