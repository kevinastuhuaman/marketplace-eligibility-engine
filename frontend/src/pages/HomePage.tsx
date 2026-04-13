import { ProductGrid } from "../components/customer/ProductGrid";

export function HomePage() {
  return (
    <div className="max-w-screen-xl mx-auto px-4 py-6">
      <h2 className="text-xl font-bold text-brand-gray-900 mb-4">
        Shop All Products
      </h2>
      <ProductGrid />
    </div>
  );
}
