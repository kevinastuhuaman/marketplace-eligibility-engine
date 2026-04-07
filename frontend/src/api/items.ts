import { apiFetch } from "./client";
import type { Item } from "../types/api";

export function fetchItems(): Promise<Item[]> {
  return apiFetch<Item[]>("/v1/items");
}

export function fetchItem(itemId: string): Promise<Item> {
  return apiFetch<Item>(`/v1/items/${itemId}`);
}
