import clsx from "clsx";
import type { PathResult } from "../../types/api";
import { AlternativeNodeList } from "./AlternativeNodeList";
import { AvailabilityConfidenceBadge } from "./AvailabilityConfidenceBadge";
import { RestrictionZoneMap } from "./RestrictionZoneMap";
import { StatusBadge } from "../shared/StatusBadge";

const PATH_LABELS: Record<string, string> = {
  ship_to_home: "Ship to Home",
  pickup: "Pickup",
  ship_from_store: "Ship from Store",
  marketplace_3p: "Marketplace (3P)",
};

const PATH_ICONS: Record<string, string> = {
  ship_to_home: "🚚",
  pickup: "🏬",
  ship_from_store: "📦",
  marketplace_3p: "🏪",
};

export function FulfillmentPaths({ paths }: { paths: PathResult[] }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-brand-gray-700">Fulfillment Paths</h3>
      <div className="grid grid-cols-2 gap-2">
        {paths.map((p) => (
          <div
            key={p.path_code}
            className={clsx(
              "rounded-lg border p-3",
              p.status === "clear" && "border-green-300 bg-green-50",
              p.status === "conditional" && "border-yellow-300 bg-yellow-50",
              p.status === "gated" && "border-orange-300 bg-orange-50",
              p.status === "blocked" && "border-red-300 bg-red-50",
              p.status === "low_confidence" && "border-amber-300 bg-amber-50"
            )}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium">
                {PATH_ICONS[p.path_code]} {PATH_LABELS[p.path_code] ?? p.path_code}
              </span>
              <StatusBadge status={p.status} />
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <AvailabilityConfidenceBadge
                band={p.confidence_band}
                score={p.confidence_score}
              />
              {p.fallback_applied && (
                <span className="text-[10px] font-semibold uppercase tracking-wide text-brand-gray-500">
                  Fallback applied
                </span>
              )}
            </div>
            {p.inventory_available != null && (
              <p className="text-xs text-brand-gray-500">
                Stock: {p.inventory_available}
              </p>
            )}
            {p.confidence_reason && (
              <p className="text-xs text-brand-gray-500 mt-1">{p.confidence_reason}</p>
            )}
            {p.violations.length > 0 && (
              <p className="text-xs text-red-700 mt-1 line-clamp-2">
                {p.violations[0].reason}
              </p>
            )}
            {p.requirements.length > 0 && (
              <p className="text-xs text-yellow-700 mt-1 line-clamp-2">
                {p.requirements[0].reason}
              </p>
            )}
            {p.gates.length > 0 && (
              <p className="text-xs text-orange-700 mt-1 line-clamp-2">
                {p.gates[0].reason}
              </p>
            )}
            {p.fallback_reason && (
              <p className="mt-1 text-xs text-brand-gray-500">{p.fallback_reason}</p>
            )}
            <AlternativeNodeList nodes={p.alternative_nodes} />
            <RestrictionZoneMap path={p} />
          </div>
        ))}
      </div>
    </div>
  );
}
