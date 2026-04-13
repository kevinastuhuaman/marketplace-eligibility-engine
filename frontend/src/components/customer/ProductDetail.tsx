import { useState, useEffect } from "react";
import type { Item } from "../../types/api";
import { diagnoseEligibility } from "../../api/diagnose";
import { useMarketStore } from "../../store/market-store";
import { useEvaluationStore } from "../../store/evaluation-store";
import { useUiStore } from "../../store/ui-store";
import { evaluateEligibility } from "../../api/evaluate";
import { diagnosisLocaleForMarket } from "../../lib/markets";
import { DiagnosisTimeline } from "./DiagnosisTimeline";
import { MarketComparisonPanel } from "./MarketComparisonPanel";
import { SellerPicker } from "./SellerPicker";
import { QuantitySelector } from "./QuantitySelector";
import { FulfillmentPaths } from "./FulfillmentPaths";
import { EligibilityBadge } from "../shared/StatusBadge";
import type { SellerPerformanceMetric, SellerPerformanceSignal } from "../../types/api";

const sellerMetricShortLabels: Record<string, string> = {
  cancellation_rate: "Cancel",
  on_time_delivery_rate: "OTD",
  valid_tracking_rate: "Tracking",
  seller_response_rate: "Response",
  return_rate: "Returns",
  item_not_received_rate: "INR",
  negative_feedback_rate: "Negative FB",
};

function formatRate(value: number) {
  return `${(value * 100).toFixed(value * 100 < 10 ? 1 : 0)}%`;
}

function formatThreshold(metric: SellerPerformanceMetric) {
  const qualifier = metric.direction === "max" ? "max" : "min";
  return `${qualifier} ${formatRate(metric.threshold)}`;
}

function SellerPerformanceCard({
  performance,
  signal,
}: {
  performance: SellerPerformanceSignal;
  signal?: { ipi_score: number; ipi_tier: string; rank_adjustment_pct: number; wfs_recommendation?: string | null } | null;
}) {
  const statusTone =
    performance.overall_status === "good_standing"
      ? "border-emerald-200 bg-emerald-50"
      : "border-orange-200 bg-orange-50";
  const badgeTone =
    performance.overall_status === "good_standing"
      ? "bg-emerald-100 text-emerald-800"
      : "bg-orange-100 text-orange-900";

  return (
    <div className={`rounded-lg border p-3 ${statusTone}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-brand-gray-500">
            Marketplace Performance
          </p>
          <p className="mt-1 text-sm text-brand-gray-900">
            Marketplace standards updated {performance.standards_last_updated}
          </p>
        </div>
        <span className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wide ${badgeTone}`}>
          {performance.overall_status === "good_standing" ? "Good standing" : "Action required"}
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {performance.uses_wfs && (
          <span className="rounded-full bg-brand-blue-light px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-brand-blue-dark">
            Platform fulfillment
          </span>
        )}
        {performance.pro_seller_eligible && (
          <span className="rounded-full bg-emerald-100 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-emerald-800">
            Pro Seller ready
          </span>
        )}
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
        {performance.metrics.map((metric) => (
          <div
            key={metric.code}
            className="rounded-md border border-white/70 bg-white/80 p-2"
          >
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-brand-gray-500">
                {sellerMetricShortLabels[metric.code] ?? metric.label}
              </p>
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                  metric.status === "meets_standard"
                    ? "bg-emerald-100 text-emerald-800"
                    : "bg-orange-100 text-orange-900"
                }`}
              >
                {metric.status === "meets_standard" ? "Meets" : "Misses"}
              </span>
            </div>
            <p className="mt-1 text-sm font-semibold text-brand-gray-900">
              {formatRate(metric.actual)}
            </p>
            <p className="text-xs text-brand-gray-500">{formatThreshold(metric)}</p>
            {metric.wfs_assisted && (
              <p className="mt-1 text-[11px] text-brand-blue-dark">Platform fulfillment helps cover this metric.</p>
            )}
          </div>
        ))}
      </div>

      <p className="mt-3 text-xs text-brand-gray-600">{performance.account_risk}</p>

      {signal && (
        <div className="mt-3 rounded-md border border-brand-gray-200 bg-white/80 p-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-brand-gray-500">
            Secondary internal signal
          </p>
          <p className="mt-1 text-sm text-brand-gray-900">
            Composite {signal.ipi_score} · {signal.ipi_tier}
          </p>
          {signal.wfs_recommendation && (
            <p className="mt-1 text-xs text-brand-gray-500">{signal.wfs_recommendation}</p>
          )}
        </div>
      )}
    </div>
  );
}

export function ProductDetail({ item }: { item: Item }) {
  const market = useMarketStore((s) => s.market);
  const diagnosisLocale = useUiStore((s) => s.diagnosisLocale);
  const {
    response,
    setResponse,
    request,
    setRequest,
    diagnosis,
    setDiagnosis,
    isEvaluating,
    setIsEvaluating,
    isDiagnosing,
    setIsDiagnosing,
    testerMode,
    scenarioContext,
    setScenarioContext,
  } = useEvaluationStore();
  const [sellerId, setSellerId] = useState<string | null>(null);
  const [age, setAge] = useState<number | undefined>(undefined);
  const [quantity, setQuantity] = useState(1);
  const [scenarioLocation, setScenarioLocation] = useState<{
    state?: string;
    zip?: string;
    county?: string | null;
    latitude?: number | null;
    longitude?: number | null;
    address_id?: string | null;
  } | null>(null);
  const [scenarioPrimaryNodeId, setScenarioPrimaryNodeId] = useState<string | null>(
    null,
  );
  const [scenarioNearbyNodes, setScenarioNearbyNodes] = useState<string[]>([]);
  const activeRequest = request;

  // Sync controls when a scenario sets context
  useEffect(() => {
    if (scenarioContext) {
      setSellerId(scenarioContext.sellerId);
      setAge(scenarioContext.age);
      setQuantity(scenarioContext.quantity ?? 1);
      setScenarioLocation(scenarioContext.location ?? null);
      setScenarioPrimaryNodeId(scenarioContext.primaryNodeId ?? null);
      setScenarioNearbyNodes(scenarioContext.nearbyNodes ?? []);
      setScenarioContext(null);
    }
  }, [scenarioContext, setScenarioContext]);

  useEffect(() => {
    const shouldDiagnose =
      !!activeRequest &&
      !!response &&
      response.item_id === item.item_id &&
      !response.errors.length &&
      response.paths.some((path) => path.status === "blocked" || path.status === "gated");

    if (!shouldDiagnose) {
      setDiagnosis(null);
      setIsDiagnosing(false);
      return;
    }

    let cancelled = false;

    async function runDiagnosis() {
      setIsDiagnosing(true);
      try {
        const requestForDiagnosis = activeRequest;
        if (!requestForDiagnosis) {
          return;
        }
        const result = await diagnoseEligibility({
          ...requestForDiagnosis,
          locale:
            diagnosisLocale === "auto"
              ? diagnosisLocaleForMarket(requestForDiagnosis.market_code)
              : diagnosisLocale,
        });
        if (!cancelled) {
          setDiagnosis(result);
        }
      } catch {
        if (!cancelled) {
          setDiagnosis(null);
        }
      } finally {
        if (!cancelled) {
          setIsDiagnosing(false);
        }
      }
    }

    void runDiagnosis();

    return () => {
      cancelled = true;
    };
  }, [
    diagnosisLocale,
    item.item_id,
    activeRequest,
    response,
    setDiagnosis,
    setIsDiagnosing,
  ]);

  const hasAgeRestriction = item.compliance_tags.includes("age_restricted");
  const hasQuantityLimit = item.compliance_tags.includes("quantity_limited");

  async function handleEvaluate() {
    setIsEvaluating(true);
    setDiagnosis(null);
    try {
      const evaluationRequest = {
        item_id: item.item_id,
        market_code: market.code,
        customer_location: {
          state: scenarioLocation?.state ?? market.state,
          zip: scenarioLocation?.zip ?? market.zip,
          county: scenarioLocation?.county ?? null,
          latitude: scenarioLocation?.latitude ?? null,
          longitude: scenarioLocation?.longitude ?? null,
          address_id: scenarioLocation?.address_id ?? null,
        },
        seller_id: sellerId,
        timestamp: new Date().toISOString(),
        context: {
          customer_age: age,
          requested_quantity: hasQuantityLimit ? quantity : undefined,
          primary_node_id: scenarioPrimaryNodeId ?? undefined,
          nearby_nodes: scenarioNearbyNodes.length ? scenarioNearbyNodes : undefined,
        },
      };
      setRequest(evaluationRequest);
      const result = await evaluateEligibility(evaluationRequest, testerMode);
      setResponse(result);
    } finally {
      setIsEvaluating(false);
    }
  }

  return (
    <div className="flex flex-col gap-6 md:flex-row md:gap-8">
      <div className="flex aspect-square w-full max-w-xs flex-shrink-0 self-center items-center justify-center rounded-xl bg-brand-gray-50 text-7xl sm:max-w-sm md:h-64 md:w-64 md:max-w-none md:self-start md:text-8xl">
        {item.display_metadata.emoji || "📦"}
      </div>

      <div className="min-w-0 flex-1 space-y-4">
        <div>
          <p className="text-xs text-brand-gray-500 font-mono">{item.sku}</p>
          <h1 className="text-2xl font-bold text-brand-gray-900">{item.name}</h1>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-brand-blue-light px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-brand-blue-dark">
              {market.display_name}
            </span>
            <span className="rounded-full bg-brand-gray-100 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-brand-gray-700">
              {market.country_label}
            </span>
          </div>
          {item.category_path && (
            <p className="text-sm text-brand-gray-500 mt-1">
              {item.category_path.split(".").join(" > ")}
            </p>
          )}
        </div>

        {item.display_metadata.price && (
          <p className="text-3xl font-bold text-brand-gray-900">
            ${item.display_metadata.price}
          </p>
        )}

        {item.display_metadata.description && (
          <p className="text-sm text-brand-gray-500">
            {item.display_metadata.description}
          </p>
        )}

        <div className="flex flex-wrap gap-1.5">
          {item.compliance_tags.map((tag) => (
            <span
              key={tag}
              className="px-2 py-1 text-xs font-medium rounded-full bg-brand-blue-light text-brand-blue-dark"
            >
              {tag}
            </span>
          ))}
        </div>

        <div className="border-t border-brand-gray-200 pt-4 space-y-3">
          <SellerPicker itemId={item.item_id} value={sellerId} onChange={setSellerId} />

          {hasAgeRestriction && (
            <div>
              <label className="block text-sm font-medium text-brand-gray-700 mb-1">
                Customer Age
              </label>
              <input
                type="number"
                min={1}
                max={120}
                value={age ?? ""}
                onChange={(e) => setAge(e.target.value ? Number(e.target.value) : undefined)}
                placeholder="Enter age for verification"
                className="w-32 px-3 py-2 border border-brand-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-blue"
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
          className="w-full py-3 px-6 bg-brand-blue text-white font-bold rounded-full hover:bg-brand-blue-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isEvaluating ? "Evaluating..." : "Check Eligibility"}
        </button>

        {response && response.item_id === item.item_id && (
          <div className="space-y-3 border-t border-brand-gray-200 pt-4">
            <div className="flex items-center justify-between">
              <EligibilityBadge eligible={response.eligible} />
              <span className="text-xs text-brand-gray-500">
                {response.rules_loaded} rules loaded, {response.evaluation_ms}ms
              </span>
            </div>

            {response.market_summary && (
              <div className="rounded-lg border border-brand-gray-200 bg-brand-gray-50 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-gray-500">
                  Market Summary
                </p>
                <p className="mt-1 text-sm text-brand-gray-900">
                  {response.market_summary.display_name} · {response.market_summary.currency_code}
                </p>
              </div>
            )}

            {response.seller_performance && (
              <SellerPerformanceCard
                performance={response.seller_performance}
                signal={response.seller_signal ?? null}
              />
            )}

            {!response.seller_performance && response.seller_signal && (
              <div className="rounded-lg border border-brand-gray-200 bg-brand-gray-50 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-gray-500">
                  Secondary internal signal
                </p>
                <p className="mt-1 text-sm text-brand-gray-900">
                  Composite {response.seller_signal.ipi_score} · {response.seller_signal.ipi_tier}
                </p>
                {response.seller_signal.wfs_recommendation && (
                  <p className="mt-1 text-xs text-brand-gray-500">
                    {response.seller_signal.wfs_recommendation}
                  </p>
                )}
              </div>
            )}

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

            <DiagnosisTimeline diagnosis={diagnosis} isLoading={isDiagnosing} />

            <MarketComparisonPanel itemId={item.item_id} />
          </div>
        )}
      </div>
    </div>
  );
}
