import clsx from "clsx";
import type { PathResult } from "../../types/api";

const PATH_LABELS: Record<string, string> = {
  ship_to_home: "Ship to Home",
  pickup: "Pickup",
  ship_from_store: "Ship from Store",
  marketplace_3p: "Marketplace 3P",
};

const STATUS_COLORS: Record<string, string> = {
  clear: "bg-green-500",
  conditional: "bg-yellow-500",
  gated: "bg-orange-500",
  blocked: "bg-red-500",
};

const STATUS_RING: Record<string, string> = {
  clear: "ring-green-500/30",
  conditional: "ring-yellow-500/30",
  gated: "ring-orange-500/30",
  blocked: "ring-red-500/30",
};

export function FulfillmentDiagram({ paths }: { paths: PathResult[] }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-bold text-white">Fulfillment Paths</h3>
      <div className="grid grid-cols-4 gap-2">
        {paths.map((p) => (
          <div
            key={p.path_code}
            className="bg-debug-surface border border-debug-border rounded-lg p-3 text-center"
          >
            <div className="flex justify-center mb-2">
              <div
                className={clsx(
                  "w-8 h-8 rounded-full ring-4",
                  STATUS_COLORS[p.status],
                  STATUS_RING[p.status]
                )}
              />
            </div>
            <p className="text-xs font-medium text-white">
              {PATH_LABELS[p.path_code] ?? p.path_code}
            </p>
            <p className="text-[10px] text-gray-400 uppercase font-semibold mt-0.5">
              {p.status}
            </p>
            {p.inventory_available != null && (
              <p className="text-[10px] text-gray-500 mt-1">
                Stock: {p.inventory_available}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
