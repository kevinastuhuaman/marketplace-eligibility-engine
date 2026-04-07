import { useState } from "react";
import type { Item } from "../../types/api";
import { useMarketStore } from "../../store/market-store";
import { useEvaluationStore } from "../../store/evaluation-store";
import { evaluateEligibility } from "../../api/evaluate";
import { SellerPicker } from "./SellerPicker";
import { QuantitySelector } from "./QuantitySelector";
import { FulfillmentPaths } from "./FulfillmentPaths";
import { EligibilityBadge } from "../shared/StatusBadge";

export function ProductDetail({ item }: { item: Item }) {
  const market = useMarketStore((s) => s.market);
  const { response, setResponse, isEvaluating, setIsEvaluating, testerMode } = useEvaluationStore();
  const [sellerId, setSellerId] = useState<string | null>(null);
  const [age, setAge] = useState<number | undefined>(undefined);
  const [quantity, setQuantity] = useState(1);

  const hasAgeRestriction = item.compliance_tags.includes("age_restricted");
  const hasQuantityLimit = item.compliance_tags.includes("quantity_limited");

  async function handleEvaluate() {
    setIsEvaluating(true);
    try {
      const result = await evaluateEligibility(
        {
          item_id: item.item_id,
          market_code: market.code,
          customer_location: { state: market.state, zip: market.zip },
          seller_id: sellerId,
          timestamp: new Date().toISOString(),
          context: {
            customer_age: age,
            requested_quantity: hasQuantityLimit ? quantity : undefined,
          },
        },
        testerMode,
      );
      setResponse(result);
    } finally {
      setIsEvaluating(false);
    }
  }

  return (
    <div className="flex gap-8">
      <div className="flex-shrink-0 w-64 h-64 bg-walmart-gray-50 rounded-xl flex items-center justify-center text-8xl">
        {item.display_metadata.emoji || "📦"}
      </div>

      <div className="flex-1 space-y-4">
        <div>
          <p className="text-xs text-walmart-gray-500 font-mono">{item.sku}</p>
          <h1 className="text-2xl font-bold text-walmart-gray-900">{item.name}</h1>
          {item.category_path && (
            <p className="text-sm text-walmart-gray-500 mt-1">
              {item.category_path.split(".").join(" > ")}
            </p>
          )}
        </div>

        {item.display_metadata.price && (
          <p className="text-3xl font-bold text-walmart-gray-900">
            ${item.display_metadata.price}
          </p>
        )}

        {item.display_metadata.description && (
          <p className="text-sm text-walmart-gray-500">
            {item.display_metadata.description}
          </p>
        )}

        <div className="flex flex-wrap gap-1.5">
          {item.compliance_tags.map((tag) => (
            <span
              key={tag}
              className="px-2 py-1 text-xs font-medium rounded-full bg-walmart-blue-light text-walmart-blue-dark"
            >
              {tag}
            </span>
          ))}
        </div>

        <div className="border-t border-walmart-gray-200 pt-4 space-y-3">
          <SellerPicker itemId={item.item_id} value={sellerId} onChange={setSellerId} />

          {hasAgeRestriction && (
            <div>
              <label className="block text-sm font-medium text-walmart-gray-700 mb-1">
                Customer Age
              </label>
              <input
                type="number"
                min={1}
                max={120}
                value={age ?? ""}
                onChange={(e) => setAge(e.target.value ? Number(e.target.value) : undefined)}
                placeholder="Enter age for verification"
                className="w-32 px-3 py-2 border border-walmart-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-walmart-blue"
              />
            </div>
          )}

          {hasQuantityLimit && (
            <QuantitySelector value={quantity} onChange={setQuantity} />
          )}
        </div>

        <button
          onClick={handleEvaluate}
          disabled={isEvaluating}
          className="w-full py-3 px-6 bg-walmart-blue text-white font-bold rounded-full hover:bg-walmart-blue-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isEvaluating ? "Evaluating..." : "Check Eligibility"}
        </button>

        {response && response.item_id === item.item_id && (
          <div className="space-y-3 border-t border-walmart-gray-200 pt-4">
            <div className="flex items-center justify-between">
              <EligibilityBadge eligible={response.eligible} />
              <span className="text-xs text-walmart-gray-500">
                {response.rules_loaded} rules loaded, {response.evaluation_ms}ms
              </span>
            </div>

            {response.warnings.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                {response.warnings.map((w) => (
                  <p key={w.rule_id} className="text-sm text-yellow-800">
                    ⚠️ {w.reason}
                  </p>
                ))}
              </div>
            )}

            {response.errors.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                {response.errors.map((e, i) => (
                  <p key={i} className="text-sm text-red-800">{e}</p>
                ))}
              </div>
            )}

            <FulfillmentPaths paths={response.paths} />
          </div>
        )}
      </div>
    </div>
  );
}
