import { Link } from "react-router-dom";
import type { Item } from "../../types/api";

export function ProductCard({ item }: { item: Item }) {
  const { emoji, price } = item.display_metadata;

  return (
    <Link
      to={`/product/${item.item_id}`}
      className="bg-white border border-brand-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow group"
    >
      <div className="flex items-center justify-center h-32 bg-brand-gray-50 rounded-lg mb-3 text-5xl group-hover:scale-105 transition-transform">
        {emoji || "📦"}
      </div>
      <div className="space-y-1">
        <p className="text-xs text-brand-gray-500 font-mono">{item.sku}</p>
        <h3 className="text-sm font-semibold text-brand-gray-900 line-clamp-2 leading-tight">
          {item.name}
        </h3>
        {price && (
          <p className="text-lg font-bold text-brand-gray-900">
            ${price}
          </p>
        )}
        <div className="flex flex-wrap gap-1 pt-1">
          {item.compliance_tags.map((tag) => (
            <span
              key={tag}
              className="px-1.5 py-0.5 text-[10px] font-medium rounded bg-brand-blue-light text-brand-blue-dark"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </Link>
  );
}
