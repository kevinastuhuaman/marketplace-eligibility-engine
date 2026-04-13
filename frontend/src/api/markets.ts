import { apiFetch } from "./client";
import type { MarketDefinition } from "../types/api";

export function fetchMarkets(): Promise<MarketDefinition[]> {
  return apiFetch<MarketDefinition[]>("/v1/markets");
}
