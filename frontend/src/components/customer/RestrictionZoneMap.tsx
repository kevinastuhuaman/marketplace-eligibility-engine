import type { PathResult } from "../../types/api";

export function RestrictionZoneMap({ path }: { path: PathResult }) {
  if (!path.matched_zone_codes.length) {
    return null;
  }

  return (
    <div className="mt-2 rounded-md border border-red-200 bg-red-50 p-3">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-red-900">
        Restricted Zone
      </p>
      <svg
        viewBox="0 0 220 120"
        className="mt-2 h-28 w-full rounded border border-red-200 bg-white"
        role="img"
        aria-label="Restriction zone diagram"
      >
        <polygon
          points="30,20 180,18 200,60 172,100 44,98 16,56"
          fill="#fecaca"
          stroke="#dc2626"
          strokeWidth="2"
        />
        <circle cx="110" cy="62" r="8" fill="#1d4ed8" />
        <text x="18" y="112" fontSize="10" fill="#7f1d1d">
          {path.matched_zone_codes.join(", ")}
        </text>
      </svg>
      {path.zone_explanation && (
        <p className="mt-2 text-xs text-red-900">{path.zone_explanation}</p>
      )}
    </div>
  );
}
