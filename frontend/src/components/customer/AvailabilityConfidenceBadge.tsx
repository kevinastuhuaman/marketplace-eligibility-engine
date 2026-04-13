import type { ConfidenceBand } from "../../types/api";

const BAND_COPY: Record<ConfidenceBand, string> = {
  high: "High Confidence",
  medium: "Medium Confidence",
  low: "Unverified",
};

const BAND_CLASS: Record<ConfidenceBand, string> = {
  high: "bg-emerald-100 text-emerald-800 border-emerald-300",
  medium: "bg-amber-100 text-amber-900 border-amber-300",
  low: "bg-orange-100 text-orange-900 border-orange-300",
};

export function AvailabilityConfidenceBadge({
  band,
  score,
}: {
  band?: ConfidenceBand | null;
  score?: number | null;
}) {
  if (!band) {
    return null;
  }

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${BAND_CLASS[band]}`}
    >
      {BAND_COPY[band]}
      {typeof score === "number" ? ` ${Math.round(score * 100)}%` : ""}
    </span>
  );
}
