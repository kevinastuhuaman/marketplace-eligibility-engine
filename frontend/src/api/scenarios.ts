import { apiFetch } from "./client";
import type { Scenario } from "../types/api";

export function fetchScenarios(): Promise<Scenario[]> {
  return apiFetch<Scenario[]>("/v1/demo/scenarios");
}
