import { MARKETS as LEGACY_MARKETS } from "../data/markets";
import type { DiagnosisLocale, MarketDefinition, MarketOption } from "../types/api";

const DEFAULT_SUPPORTED_PATHS = [
  "ship_to_home",
  "pickup",
  "ship_from_store",
  "marketplace_3p",
];

const COUNTRY_NAMES: Record<string, string> = {
  US: "United States",
  MX: "Mexico",
  CL: "Chile",
  CR: "Costa Rica",
  CA: "Canada",
};

const INTERNATIONAL_FALLBACKS: MarketOption[] = [
  {
    code: "MX-CDMX",
    market_code: "MX-CDMX",
    state: "CDMX",
    region_code: "CDMX",
    label: "Ciudad de Mexico",
    city: "Mexico City",
    zip: "01000",
    display_name: "Mexico City, CDMX",
    country_code: "MX",
    country_label: "Mexico",
    currency_code: "MXN",
    language_codes: ["es"],
    supported_paths: DEFAULT_SUPPORTED_PATHS,
    regulatory_summary: { spotlight: "NOM certification, IEPS, Spanish labeling" },
  },
  {
    code: "CL-RM",
    market_code: "CL-RM",
    state: "RM",
    region_code: "RM",
    label: "Region Metropolitana",
    city: "Santiago",
    zip: "8320000",
    display_name: "Santiago, Region Metropolitana",
    country_code: "CL",
    country_label: "Chile",
    currency_code: "CLP",
    language_codes: ["es"],
    supported_paths: DEFAULT_SUPPORTED_PATHS,
    regulatory_summary: { spotlight: "Black labels and lithium controls" },
  },
  {
    code: "CR-SJ",
    market_code: "CR-SJ",
    state: "SJ",
    region_code: "SJ",
    label: "San Jose",
    city: "San Jose",
    zip: "10101",
    display_name: "San Jose, Costa Rica",
    country_code: "CR",
    country_label: "Costa Rica",
    currency_code: "CRC",
    language_codes: ["es"],
    supported_paths: DEFAULT_SUPPORTED_PATHS,
    regulatory_summary: { spotlight: "RTCA and VAT registration" },
  },
  {
    code: "CA-ON",
    market_code: "CA-ON",
    state: "ON",
    region_code: "ON",
    label: "Ontario",
    city: "Toronto",
    zip: "M5H",
    display_name: "Toronto, Ontario",
    country_code: "CA",
    country_label: "Canada",
    currency_code: "CAD",
    language_codes: ["en", "fr"],
    supported_paths: DEFAULT_SUPPORTED_PATHS,
    regulatory_summary: { spotlight: "Bilingual labeling and metric units" },
  },
];

const US_FALLBACKS: MarketOption[] = LEGACY_MARKETS.map((market) => ({
  code: market.code,
  market_code: market.code,
  state: market.state,
  region_code: market.state,
  label: market.label,
  city: market.city,
  zip: market.zip,
  display_name: `${market.city}, ${market.label}`,
  country_code: "US",
  country_label: "United States",
  currency_code: "USD",
  language_codes: ["en"],
  supported_paths: DEFAULT_SUPPORTED_PATHS,
  regulatory_summary: { spotlight: "US market defaults" },
}));

export const FALLBACK_MARKETS: MarketOption[] = [
  ...US_FALLBACKS,
  ...INTERNATIONAL_FALLBACKS,
];

function countryLabel(countryCode: string): string {
  return COUNTRY_NAMES[countryCode] ?? countryCode;
}

export function toMarketOption(definition: MarketDefinition): MarketOption {
  const fallback = FALLBACK_MARKETS.find(
    (market) => market.code === definition.market_code,
  );

  return {
    code: definition.market_code,
    market_code: definition.market_code,
    state: definition.region_code,
    region_code: definition.region_code,
    label: fallback?.label ?? definition.region_code,
    city: fallback?.city ?? definition.display_name.split(",")[0] ?? definition.region_code,
    zip: fallback?.zip ?? "00000",
    display_name: definition.display_name,
    country_code: definition.country_code,
    country_label: countryLabel(definition.country_code),
    currency_code: definition.currency_code,
    language_codes: definition.language_codes,
    supported_paths: definition.supported_paths,
    regulatory_summary: definition.regulatory_summary,
  };
}

export function mergeMarketDefinitions(
  definitions?: MarketDefinition[],
): MarketOption[] {
  const normalized = (definitions ?? []).map(toMarketOption);
  const presentCodes = new Set(normalized.map((market) => market.code));

  return [
    ...normalized,
    ...FALLBACK_MARKETS.filter((market) => !presentCodes.has(market.code)),
  ];
}

export function resolveMarketOption(
  marketCode?: string,
  availableMarkets: MarketOption[] = FALLBACK_MARKETS,
): MarketOption {
  if (!marketCode) {
    return availableMarkets[1] ?? availableMarkets[0];
  }

  return (
    availableMarkets.find((market) => market.code === marketCode) ??
    FALLBACK_MARKETS.find((market) => market.code === marketCode) ??
    availableMarkets[0] ??
    FALLBACK_MARKETS[0]
  );
}

export function diagnosisLocaleForMarket(marketCode: string): DiagnosisLocale {
  return /^(MX|CL|CR)-/.test(marketCode) ? "es" : "en";
}
