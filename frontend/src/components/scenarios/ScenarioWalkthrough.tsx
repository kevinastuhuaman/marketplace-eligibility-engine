import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchScenarios } from "../../api/scenarios";
import { useUiStore } from "../../store/ui-store";
import { ScenarioNarrationPanel } from "./ScenarioNarrationPanel";

export function ScenarioWalkthrough() {
  const { data: scenarios } = useQuery({
    queryKey: ["scenarios"],
    queryFn: fetchScenarios,
  });
  const autoplay = useUiStore((state) => state.walkthroughAutoplay);
  const setAutoplay = useUiStore((state) => state.setWalkthroughAutoplay);
  const [index, setIndex] = useState(0);

  const scenario = useMemo(() => scenarios?.[index] ?? null, [index, scenarios]);

  useEffect(() => {
    if (!autoplay || !scenarios?.length) {
      return;
    }
    const timer = window.setInterval(() => {
      setIndex((current) => (current + 1) % scenarios.length);
    }, 4000);
    return () => window.clearInterval(timer);
  }, [autoplay, scenarios]);

  if (!scenario) {
    return <div className="text-sm text-walmart-gray-500">Loading scenarios...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-walmart-gray-900">
          {scenario.id}. {scenario.short_label}
        </p>
        <button
          type="button"
          onClick={() => setAutoplay(!autoplay)}
          className="rounded-full border border-walmart-gray-300 px-3 py-1 text-xs font-semibold text-walmart-gray-700"
        >
          {autoplay ? "Pause" : "Autoplay"}
        </button>
      </div>

      <ScenarioNarrationPanel
        title={scenario.label}
        narration={scenario.narration}
        whatItProves={scenario.what_it_proves}
      />

      <div className="grid gap-3 md:grid-cols-2">
        {scenario.variants.map((variant) => (
          <div key={variant.label} className="rounded-lg border border-walmart-gray-200 bg-white p-4">
            <p className="text-sm font-semibold text-walmart-gray-900">{variant.label}</p>
            <p className="mt-1 text-xs text-walmart-gray-500">
              {variant.market_code} · {variant.item_sku}
            </p>
            <p className="mt-2 text-sm text-walmart-gray-700">{variant.expected_outcome}</p>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        {(scenarios ?? []).map((entry, entryIndex) => (
          <button
            key={entry.id}
            type="button"
            onClick={() => setIndex(entryIndex)}
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              entryIndex === index
                ? "bg-walmart-blue text-white"
                : "border border-walmart-gray-300 text-walmart-gray-700"
            }`}
          >
            {entry.id}
          </button>
        ))}
      </div>
    </div>
  );
}
