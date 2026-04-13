import { apiFetch } from "./client";
import type { DiagnosisRequest, DiagnosisResponse } from "../types/api";

export function diagnoseEligibility(
  request: DiagnosisRequest,
): Promise<DiagnosisResponse> {
  return apiFetch<DiagnosisResponse>("/v1/diagnose", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
