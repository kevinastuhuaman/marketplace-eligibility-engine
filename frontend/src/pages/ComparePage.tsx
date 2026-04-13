import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { evaluateEligibility } from "../api/evaluate";
import { fetchItem } from "../api/items";
import { useMarketStore } from "../store/market-store";
import { useUiStore } from "../store/ui-store";
import type { EligibilityResponse } from "../types/api";
import { StatusBadge } from "../components/shared/StatusBadge";

export function ComparePage() {
  const { id } = useParams<{ id: string }>();
  const { data: item } = useQuery({
    queryKey: ["compare-item", id],
    queryFn: () => fetchItem(id!),
    enabled: !!id,
  });
  const markets = useMarketStore((state) => state.markets);
  const compareMarketCodes = useUiStore((state) => state.compareMarketCodes);
  const [results, setResults] = useState<Record<string, EligibilityResponse>>({});

  useEffect(() => {
    const currentItem = item;
    if (!currentItem) {
      return;
    }
    let cancelled = false;
    async function run() {
      const entries = await Promise.all(
        compareMarketCodes.map(async (marketCode) => {
          const market = markets.find((entry) => entry.code === marketCode);
          if (!market) {
            return null;
          }
          const result = await evaluateEligibility({
            item_id: currentItem!.item_id,
            market_code: market.code,
            customer_location: { state: market.state, zip: market.zip },
            timestamp: new Date().toISOString(),
            context: { customer_age: 25 },
          });
          return [market.code, result] as const;
        }),
      );
      if (!cancelled) {
        setResults(
          Object.fromEntries(entries.filter((entry): entry is readonly [string, EligibilityResponse] => !!entry)),
        );
      }
    }
    void run();
    return () => {
      cancelled = true;
    };
  }, [compareMarketCodes, item, markets]);

  return (
    <div className="max-w-screen-xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-walmart-gray-900">Market Comparison</h1>
      <p className="mt-2 text-sm text-walmart-gray-500">
        {item ? `${item.name} across selected markets` : "Loading item..."}
      </p>
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        {compareMarketCodes.map((marketCode) => {
          const result = results[marketCode];
          const market = markets.find((entry) => entry.code === marketCode);
          return (
            <div key={marketCode} className="rounded-xl border border-walmart-gray-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-walmart-gray-500">
                {marketCode}
              </p>
              <p className="mt-1 text-sm font-semibold text-walmart-gray-900">
                {market?.display_name ?? marketCode}
              </p>
              {result ? (
                <div className="mt-3 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-walmart-gray-600">
                      {result.eligible ? "Eligible" : "Blocked"}
                    </span>
                    <StatusBadge status={result.paths[0]?.status ?? "blocked"} />
                  </div>
                  {result.warnings.slice(0, 2).map((warning) => (
                    <p key={warning.rule_name} className="text-xs text-walmart-gray-500">
                      {warning.reason}
                    </p>
                  ))}
                  {result.paths.slice(0, 2).map((path) => (
                    <p key={path.path_code} className="text-xs text-walmart-gray-700">
                      {path.path_code}: {path.status}
                    </p>
                  ))}
                </div>
              ) : (
                <p className="mt-3 text-sm text-walmart-gray-500">Evaluating...</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
