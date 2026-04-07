import { create } from "zustand";
import type { EligibilityResponse } from "../types/api";

interface ScenarioContext {
  sellerId: string | null;
  age?: number;
  quantity?: number;
}

interface EvaluationState {
  testerMode: boolean;
  toggleTesterMode: () => void;
  response: EligibilityResponse | null;
  setResponse: (r: EligibilityResponse | null) => void;
  isEvaluating: boolean;
  setIsEvaluating: (v: boolean) => void;
  scenarioContext: ScenarioContext | null;
  setScenarioContext: (ctx: ScenarioContext | null) => void;
}

export const useEvaluationStore = create<EvaluationState>()((set) => ({
  testerMode: false,
  toggleTesterMode: () => set((s) => ({ testerMode: !s.testerMode })),
  response: null,
  setResponse: (response) => set({ response }),
  isEvaluating: false,
  setIsEvaluating: (isEvaluating) => set({ isEvaluating }),
  scenarioContext: null,
  setScenarioContext: (scenarioContext) => set({ scenarioContext }),
}));
