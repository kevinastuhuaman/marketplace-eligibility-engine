import { create } from "zustand";
import { persist } from "zustand/middleware";
import { MARKETS, type Market } from "../data/markets";

interface MarketState {
  market: Market;
  setMarket: (market: Market) => void;
}

export const useMarketStore = create<MarketState>()(
  persist(
    (set) => ({
      market: MARKETS[1], // default: Texas
      setMarket: (market) => set({ market }),
    }),
    { name: "walmart-market" }
  )
);
