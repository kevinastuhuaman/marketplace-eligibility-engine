import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchItems } from "../../api/items";
import { ProductCard } from "./ProductCard";

export function ProductGrid() {
  const [search, setSearch] = useState("");
  const { data: items, isLoading, error } = useQuery({
    queryKey: ["items"],
    queryFn: fetchItems,
  });

  const filtered = items?.filter(
    (item) =>
      item.name.toLowerCase().includes(search.toLowerCase()) ||
      item.sku.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search products..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full max-w-md px-4 py-2 border border-brand-gray-200 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-transparent"
        />
      </div>

      {isLoading && (
        <div className="text-center py-12 text-brand-gray-500">Loading products...</div>
      )}
      {error && (
        <div className="text-center py-12 text-red-600">
          Failed to load products: {(error as Error).message}
        </div>
      )}
      {filtered && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {filtered.map((item) => (
            <ProductCard key={item.item_id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
