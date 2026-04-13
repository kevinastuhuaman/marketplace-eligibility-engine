import { useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchScenarios } from "../api/scenarios";

export function PrintScenarioPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const { data: scenarios } = useQuery({
    queryKey: ["scenarios"],
    queryFn: fetchScenarios,
  });

  const scenario = useMemo(
    () => scenarios?.find((entry) => entry.id === Number(scenarioId)),
    [scenarioId, scenarios],
  );

  if (!scenario) {
    return <div className="max-w-screen-lg mx-auto px-4 py-6">Loading scenario...</div>;
  }

  return (
    <div className="max-w-screen-lg mx-auto px-4 py-8 print:px-0">
      <h1 className="text-3xl font-bold text-walmart-gray-900">
        {scenario.id}. {scenario.label}
      </h1>
      <p className="mt-2 text-sm text-walmart-gray-600">{scenario.what_it_proves}</p>
      {scenario.narration && (
        <p className="mt-2 text-sm text-walmart-gray-500">{scenario.narration}</p>
      )}
      <div className="mt-6 space-y-4">
        {scenario.variants.map((variant) => (
          <div key={variant.label} className="rounded-lg border border-walmart-gray-200 p-4">
            <p className="text-sm font-semibold text-walmart-gray-900">{variant.label}</p>
            <p className="mt-1 text-xs text-walmart-gray-500">
              {variant.market_code} · {variant.item_sku}
            </p>
            <p className="mt-2 text-sm text-walmart-gray-700">{variant.expected_outcome}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
