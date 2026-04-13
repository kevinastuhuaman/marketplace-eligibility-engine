import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { MarketOption } from "../types/api";
import { FALLBACK_MARKETS, resolveMarketOption } from "../lib/markets";

interface MarketState {
  market: MarketOption;
  markets: MarketOption[];
  setMarket: (market: MarketOption) => void;
  setMarketByCode: (marketCode: string) => void;
  setMarkets: (markets: MarketOption[]) => void;
}

export const useMarketStore = create<MarketState>()(
  persist(
    (set, get) => ({
      market: resolveMarketOption("US-TX", FALLBACK_MARKETS),
      markets: FALLBACK_MARKETS,
      setMarket: (market) => set({ market }),
      setMarketByCode: (marketCode) =>
        set((state) => ({
          market: resolveMarketOption(marketCode, state.markets),
        })),
      setMarkets: (markets) => {
        const currentCode = get().market.code;
        set({
          markets,
          market: resolveMarketOption(currentCode, markets),
        });
      },
    }),
    {
      name: "walmart-market",
      partialize: (state) => ({ market: state.market }),
    },
  ),
);
