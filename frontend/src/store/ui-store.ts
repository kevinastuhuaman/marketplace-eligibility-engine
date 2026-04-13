import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { DiagnosisLocale } from "../types/api";

export type UiTheme = "light" | "night";

interface UiState {
  theme: UiTheme;
  toggleTheme: () => void;
  diagnosisLocale: DiagnosisLocale;
  setDiagnosisLocale: (locale: DiagnosisLocale) => void;
  compareMarketCodes: string[];
  setCompareMarketCodes: (codes: string[]) => void;
  walkthroughAutoplay: boolean;
  setWalkthroughAutoplay: (autoplay: boolean) => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      theme: "light",
      toggleTheme: () =>
        set((state) => ({
          theme: state.theme === "light" ? "night" : "light",
        })),
      diagnosisLocale: "auto",
      setDiagnosisLocale: (diagnosisLocale) => set({ diagnosisLocale }),
      compareMarketCodes: ["US-CA", "MX-CDMX", "CA-ON"],
      setCompareMarketCodes: (compareMarketCodes) => set({ compareMarketCodes }),
      walkthroughAutoplay: false,
      setWalkthroughAutoplay: (walkthroughAutoplay) => set({ walkthroughAutoplay }),
    }),
    {
      name: "ui",
      partialize: (state) => ({
        theme: state.theme,
        diagnosisLocale: state.diagnosisLocale,
        compareMarketCodes: state.compareMarketCodes,
        walkthroughAutoplay: state.walkthroughAutoplay,
      }),
    },
  ),
);
