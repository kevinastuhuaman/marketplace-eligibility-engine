import { apiFetch } from "./client";
import type { SellerInfo, SellerIpiResponse, SellerPerformanceResponse } from "../types/api";

export function fetchSellersForItem(itemId: string): Promise<SellerInfo[]> {
  return apiFetch<SellerInfo[]>(`/v1/sellers/for-item/${itemId}`);
}

export function fetchSellerIpi(sellerId: string): Promise<SellerIpiResponse> {
  return apiFetch<SellerIpiResponse>(`/v1/sellers/${sellerId}/ipi`);
}

export function fetchSellerPerformance(sellerId: string): Promise<SellerPerformanceResponse> {
  return apiFetch<SellerPerformanceResponse>(`/v1/sellers/${sellerId}/performance`);
}
