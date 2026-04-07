import { apiFetch } from "./client";
import type { SellerInfo } from "../types/api";

export function fetchSellersForItem(itemId: string): Promise<SellerInfo[]> {
  return apiFetch<SellerInfo[]>(`/v1/sellers/for-item/${itemId}`);
}
