import { useMarketStore } from "../../store/market-store";
import { MARKETS } from "../../data/markets";

export function LocationSelector() {
  const { market, setMarket } = useMarketStore();

  return (
    <div className="flex items-center gap-2 bg-white/10 rounded-full px-3 py-1">
      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      <select
        value={market.code}
        onChange={(e) => {
          const m = MARKETS.find((m) => m.code === e.target.value);
          if (m) setMarket(m);
        }}
        className="bg-transparent text-white text-sm border-none outline-none cursor-pointer appearance-none pr-4"
      >
        {MARKETS.map((m) => (
          <option key={m.code} value={m.code} className="text-black">
            {m.city}, {m.state}
          </option>
        ))}
      </select>
    </div>
  );
}
