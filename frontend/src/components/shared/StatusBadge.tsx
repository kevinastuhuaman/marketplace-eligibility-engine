import clsx from "clsx";

const STATUS_STYLES: Record<string, string> = {
  clear: "bg-green-100 text-green-800 border-green-300",
  conditional: "bg-yellow-100 text-yellow-800 border-yellow-300",
  gated: "bg-orange-100 text-orange-800 border-orange-300",
  blocked: "bg-red-100 text-red-800 border-red-300",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border uppercase",
        STATUS_STYLES[status] ?? "bg-gray-100 text-gray-800 border-gray-300"
      )}
    >
      {status}
    </span>
  );
}

export function EligibilityBadge({ eligible }: { eligible: boolean }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-4 py-1.5 rounded-full text-sm font-bold uppercase tracking-wide",
        eligible
          ? "bg-green-100 text-green-800 border-2 border-green-400"
          : "bg-red-100 text-red-800 border-2 border-red-400"
      )}
    >
      {eligible ? "Eligible" : "Not Eligible"}
    </span>
  );
}
