import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import { fetchScenarios } from "../../api/scenarios";
import { fetchItems } from "../../api/items";
import { evaluateEligibility } from "../../api/evaluate";
import { useMarketStore } from "../../store/market-store";
import { useEvaluationStore } from "../../store/evaluation-store";
import { MARKETS } from "../../data/markets";
import type { ScenarioVariant } from "../../types/api";

export function ScenarioStrip() {
  const [activeScenario, setActiveScenario] = useState<number | null>(null);
  const [activeVariant, setActiveVariant] = useState<number>(0);
  const navigate = useNavigate();
  const setMarket = useMarketStore((s) => s.setMarket);
  const { setResponse, setIsEvaluating, testerMode, setScenarioContext } = useEvaluationStore();
  const queryClient = useQueryClient();

  const { data: scenarios } = useQuery({
    queryKey: ["scenarios"],
    queryFn: fetchScenarios,
  });

  async function runVariant(variant: ScenarioVariant) {
    setIsEvaluating(true);
    try {
      // Resolve SKU to item_id
      let items = queryClient.getQueryData<Array<{ item_id: string; sku: string }>>(["items"]);
      if (!items) {
        items = await queryClient.fetchQuery({ queryKey: ["items"], queryFn: fetchItems });
      }
      const item = items?.find((i) => i.sku === variant.item_sku);
      if (!item) return;

      // Set market
      const market = MARKETS.find((m) => m.code === variant.market_code);
      if (market) setMarket(market);

      // Sync controls so ProductDetail reflects the scenario inputs
      setScenarioContext({
        sellerId: variant.seller_id ?? null,
        age: variant.context?.customer_age,
        quantity: variant.context?.requested_quantity,
      });

      // Navigate to product
      navigate(`/product/${item.item_id}`);

      // Evaluate
      const result = await evaluateEligibility(
        {
          item_id: item.item_id,
          market_code: variant.market_code,
          customer_location: { state: variant.state, zip: variant.zip },
          seller_id: variant.seller_id ?? null,
          timestamp: variant.timestamp ?? new Date().toISOString(),
          context: variant.context,
        },
        testerMode,
      );
      setResponse(result);
    } finally {
      setIsEvaluating(false);
    }
  }

  if (!scenarios) return null;

  const active = scenarios.find((s) => s.id === activeScenario);

  return (
    <div className="bg-walmart-gray-50 border-b border-walmart-gray-200">
      <div className="max-w-screen-2xl mx-auto px-4">
        <div className="flex items-center gap-1 py-2 overflow-x-auto">
          <span className="text-xs text-walmart-gray-500 font-medium mr-2 flex-shrink-0">
            Scenarios:
          </span>
          {scenarios.map((s) => (
            <button
              key={s.id}
              onClick={() => {
                setActiveScenario(s.id);
                setActiveVariant(0);
                runVariant(s.variants[0]);
              }}
              className={clsx(
                "px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors flex-shrink-0",
                activeScenario === s.id
                  ? "bg-walmart-blue text-white"
                  : "bg-white border border-walmart-gray-200 text-walmart-gray-700 hover:bg-walmart-gray-100"
              )}
            >
              {s.id}. {s.short_label}
            </button>
          ))}
        </div>

        {active && active.variants.length > 1 && (
          <div className="flex items-center gap-1 pb-2">
            <span className="text-[10px] text-walmart-gray-500 mr-2">Variant:</span>
            {active.variants.map((v, i) => (
              <button
                key={i}
                onClick={() => {
                  setActiveVariant(i);
                  runVariant(v);
                }}
                className={clsx(
                  "px-2 py-0.5 rounded text-[10px] font-medium transition-colors",
                  activeVariant === i
                    ? "bg-walmart-blue-dark text-white"
                    : "bg-white border border-walmart-gray-200 text-walmart-gray-600 hover:bg-walmart-gray-100"
                )}
              >
                {v.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
