import { create } from "zustand";
import type {
  DiagnosisLocale,
  DiagnosisResponse,
  EligibilityResponse,
  EvaluateRequest,
  CustomerLocation,
} from "../types/api";

interface ScenarioContext {
  sellerId: string | null;
  age?: number;
  quantity?: number;
  location?: Partial<CustomerLocation>;
  locale?: DiagnosisLocale;
  primaryNodeId?: string | null;
  nearbyNodes?: string[];
  narration?: string;
}

interface EvaluationState {
  testerMode: boolean;
  toggleTesterMode: () => void;
  response: EligibilityResponse | null;
  setResponse: (response: EligibilityResponse | null) => void;
  request: EvaluateRequest | null;
  setRequest: (request: EvaluateRequest | null) => void;
  diagnosis: DiagnosisResponse | null;
  setDiagnosis: (diagnosis: DiagnosisResponse | null) => void;
  isEvaluating: boolean;
  setIsEvaluating: (value: boolean) => void;
  isDiagnosing: boolean;
  setIsDiagnosing: (value: boolean) => void;
  scenarioContext: ScenarioContext | null;
  setScenarioContext: (context: ScenarioContext | null) => void;
  clearEvaluation: () => void;
}

export const useEvaluationStore = create<EvaluationState>()((set) => ({
  testerMode: false,
  toggleTesterMode: () => set((state) => ({ testerMode: !state.testerMode })),
  response: null,
  setResponse: (response) => set({ response }),
  request: null,
  setRequest: (request) => set({ request }),
  diagnosis: null,
  setDiagnosis: (diagnosis) => set({ diagnosis }),
  isEvaluating: false,
  setIsEvaluating: (isEvaluating) => set({ isEvaluating }),
  isDiagnosing: false,
  setIsDiagnosing: (isDiagnosing) => set({ isDiagnosing }),
  scenarioContext: null,
  setScenarioContext: (scenarioContext) => set({ scenarioContext }),
  clearEvaluation: () =>
    set({
      response: null,
      request: null,
      diagnosis: null,
      isEvaluating: false,
      isDiagnosing: false,
      scenarioContext: null,
    }),
}));
