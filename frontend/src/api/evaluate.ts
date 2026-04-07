import { apiFetch } from "./client";
import type { EvaluateRequest, EligibilityResponse } from "../types/api";

export function evaluateEligibility(
  request: EvaluateRequest,
  debug = false
): Promise<EligibilityResponse> {
  return apiFetch<EligibilityResponse>(
    `/v1/evaluate${debug ? "?debug=true" : ""}`,
    {
      method: "POST",
      body: JSON.stringify(request),
    }
  );
}
