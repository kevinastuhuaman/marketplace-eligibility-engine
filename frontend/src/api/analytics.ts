import { apiFetch, buildQueryString } from "./client";
import type {
  BlockedItemStat,
  MarketCoverageStat,
  RuleImpactStat,
} from "../types/api";

interface AnalyticsParams {
  days?: number;
  market_code?: string;
  limit?: number;
}

function unwrapList<T>(
  payload:
    | T[]
    | {
        items?: T[];
        rules?: T[];
        markets?: T[];
        results?: T[];
        data?: T[];
      },
): T[] {
  if (Array.isArray(payload)) {
    return payload;
  }

  return (
    payload.items ??
    payload.rules ??
    payload.markets ??
    payload.results ??
    payload.data ??
    []
  );
}

export async function fetchBlockedItems(
  params: AnalyticsParams = {},
): Promise<BlockedItemStat[]> {
  const payload = await apiFetch<
    BlockedItemStat[] | { items?: BlockedItemStat[]; results?: BlockedItemStat[] }
  >(
    `/v1/analytics/blocked-items${buildQueryString(
      params as Record<string, string | number | boolean | null | undefined>,
    )}`,
  );

  return unwrapList(payload);
}

export async function fetchRuleImpact(
  params: AnalyticsParams = {},
): Promise<RuleImpactStat[]> {
  const payload = await apiFetch<
    RuleImpactStat[] | { rules?: RuleImpactStat[]; results?: RuleImpactStat[] }
  >(
    `/v1/analytics/rule-impact${buildQueryString(
      params as Record<string, string | number | boolean | null | undefined>,
    )}`,
  );

  return unwrapList(payload);
}

export async function fetchMarketCoverage(
  params: AnalyticsParams = {},
): Promise<MarketCoverageStat[]> {
  const payload = await apiFetch<
    MarketCoverageStat[] | { markets?: MarketCoverageStat[]; results?: MarketCoverageStat[] }
  >(
    `/v1/analytics/market-coverage${buildQueryString(
      params as Record<string, string | number | boolean | null | undefined>,
    )}`,
  );

  return unwrapList(payload);
}
