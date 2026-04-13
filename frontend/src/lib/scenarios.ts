import type {
  CustomerLocation,
  EvaluateRequest,
  MarketOption,
  ScenarioVariant,
} from "../types/api";

export function scenarioCustomerLocation(
  variant: ScenarioVariant,
  market: MarketOption,
): CustomerLocation {
  const location = variant.customer_location ?? {};

  return {
    state: location.state ?? variant.state ?? market.state,
    zip: location.zip ?? variant.zip ?? market.zip,
    county: location.county ?? variant.county ?? null,
    latitude: location.latitude ?? null,
    longitude: location.longitude ?? null,
    address_id: location.address_id ?? null,
  };
}

export function buildScenarioRequest(
  itemId: string,
  variant: ScenarioVariant,
  market: MarketOption,
): EvaluateRequest {
  return {
    item_id: itemId,
    market_code: variant.market_code,
    customer_location: scenarioCustomerLocation(variant, market),
    seller_id: variant.seller_id ?? null,
    timestamp: variant.timestamp ?? new Date().toISOString(),
    context: {
      ...variant.context,
      primary_node_id:
        variant.primary_node_id ?? variant.context?.primary_node_id ?? undefined,
      nearby_nodes: variant.nearby_nodes ?? variant.context?.nearby_nodes ?? undefined,
    },
  };
}
