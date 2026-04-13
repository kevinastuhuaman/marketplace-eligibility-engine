import { apiFetch } from "./client";
import type {
  BatchEvaluateRequest,
  BatchEvaluateResponse,
  EligibilityResponse,
  EvaluateRequest,
} from "../types/api";

export function evaluateEligibility(
  request: EvaluateRequest,
  debug = false,
): Promise<EligibilityResponse> {
  return apiFetch<EligibilityResponse>(
    `/v1/evaluate${debug ? "?debug=true" : ""}`,
    {
      method: "POST",
      body: JSON.stringify(request),
    },
  );
}

export function batchEvaluateEligibility(
  request: BatchEvaluateRequest,
): Promise<BatchEvaluateResponse> {
  return apiFetch<BatchEvaluateResponse>("/v1/evaluate/batch", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
