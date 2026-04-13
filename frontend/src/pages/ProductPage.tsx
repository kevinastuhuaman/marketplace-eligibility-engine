import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchItem } from "../api/items";
import { ProductDetail } from "../components/customer/ProductDetail";

export function ProductPage() {
  const { id } = useParams<{ id: string }>();
  const { data: item, isLoading, error } = useQuery({
    queryKey: ["item", id],
    queryFn: () => fetchItem(id!),
    enabled: !!id,
  });

  return (
    <div className="max-w-screen-xl mx-auto px-4 py-6">
      <Link
        to="/"
        className="text-sm text-brand-blue hover:underline mb-4 inline-block"
      >
        &larr; Back to products
      </Link>

      {isLoading && (
        <div className="text-center py-12 text-brand-gray-500">Loading...</div>
      )}
      {error && (
        <div className="text-center py-12 text-red-600">
          Failed to load product: {(error as Error).message}
        </div>
      )}
      {item && <ProductDetail item={item} />}
    </div>
  );
}
