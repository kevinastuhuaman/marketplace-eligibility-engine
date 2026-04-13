import type { AlternativeNode } from "../../types/api";

export function AlternativeNodeList({ nodes }: { nodes: AlternativeNode[] }) {
  if (!nodes.length) {
    return null;
  }

  return (
    <div className="mt-2 rounded-md border border-blue-200 bg-blue-50 p-2">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-blue-900">
        Nearby Availability
      </p>
      <div className="mt-1 space-y-1">
        {nodes.map((node) => (
          <p key={node.node_id} className="text-xs text-blue-900">
            {node.node_name} · {node.distance_miles.toFixed(1)} mi · {node.available_qty} in stock
          </p>
        ))}
      </div>
    </div>
  );
}
