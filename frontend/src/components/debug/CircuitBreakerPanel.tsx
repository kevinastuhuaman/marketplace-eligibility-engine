import { useQuery } from "@tanstack/react-query";
import { fetchCircuitBreakers } from "../../api/system";

export function CircuitBreakerPanel() {
  const { data } = useQuery({
    queryKey: ["circuit-breakers"],
    queryFn: fetchCircuitBreakers,
    refetchInterval: 5000,
  });

  if (!data?.breakers?.length) {
    return null;
  }

  return (
    <div className="rounded-lg border border-debug-border bg-debug-surface p-4">
      <h3 className="text-sm font-semibold text-white">Circuit Breakers</h3>
      <div className="mt-3 space-y-2">
        {data.breakers.map((breaker) => (
          <div key={breaker.service} className="rounded border border-slate-700 p-2">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-300">
                {breaker.service}
              </p>
              <span className="text-[10px] font-semibold uppercase tracking-wide text-amber-300">
                {breaker.state}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-400">
              failures: {breaker.failure_count} · fallback: {breaker.fallback_mode}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
