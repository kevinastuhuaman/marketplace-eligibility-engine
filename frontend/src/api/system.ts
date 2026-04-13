import { apiFetch } from "./client";
import type { CircuitBreakerResponse } from "../types/api";

export function fetchCircuitBreakers(): Promise<CircuitBreakerResponse> {
  return apiFetch<CircuitBreakerResponse>("/v1/system/circuit-breakers");
}
