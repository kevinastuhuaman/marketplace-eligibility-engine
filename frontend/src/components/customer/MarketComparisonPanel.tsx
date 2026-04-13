import { Link } from "react-router-dom";
import { useUiStore } from "../../store/ui-store";

export function MarketComparisonPanel({ itemId }: { itemId: string }) {
  const compareMarketCodes = useUiStore((state) => state.compareMarketCodes);

  return (
    <div className="rounded-lg border border-walmart-gray-200 bg-walmart-gray-50 p-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-walmart-gray-500">
            Market Compare
          </p>
          <p className="mt-1 text-sm text-walmart-gray-900">
            Compare this item across {compareMarketCodes.join(", ")}
          </p>
        </div>
        <Link
          to={`/compare/${itemId}`}
          className="rounded-full bg-walmart-blue px-3 py-2 text-xs font-semibold text-white"
        >
          Open Compare
        </Link>
      </div>
    </div>
  );
}
