import { useQuery } from "@tanstack/react-query";
import { fetchSellersForItem } from "../../api/sellers";

export function SellerPicker({
  itemId,
  value,
  onChange,
}: {
  itemId: string;
  value: string | null;
  onChange: (sellerId: string | null) => void;
}) {
  const { data: sellers } = useQuery({
    queryKey: ["sellers-for-item", itemId],
    queryFn: () => fetchSellersForItem(itemId),
  });

  return (
    <div>
      <label className="block text-sm font-medium text-walmart-gray-700 mb-1">
        Seller
      </label>
      <select
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value || null)}
        className="w-full px-3 py-2 border border-walmart-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-walmart-blue"
      >
        <option value="">Walmart (1P)</option>
        {sellers?.map((s) => (
          <option key={s.seller_id} value={s.seller_id}>
            {s.name} ({s.trust_tier}
            {s.performance_status
              ? ` · ${
                  s.performance_status === "good_standing" ? "meets Walmart standards" : "action required"
                }`
              : ""}
            {s.uses_wfs ? " · WFS" : ""}
            {typeof s.ipi_score === "number" ? ` · internal ${s.ipi_score}` : ""})
          </option>
        ))}
      </select>
    </div>
  );
}
