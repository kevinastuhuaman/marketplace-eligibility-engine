import clsx from "clsx";

const ACTION_STYLES: Record<string, string> = {
  BLOCK: "bg-red-600 text-white",
  GATE: "bg-orange-500 text-white",
  REQUIRE: "bg-yellow-500 text-black",
  WARN: "bg-blue-500 text-white",
};

export function ActionBadge({ action }: { action: string }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-bold uppercase",
        ACTION_STYLES[action] ?? "bg-gray-500 text-white"
      )}
    >
      {action}
    </span>
  );
}
