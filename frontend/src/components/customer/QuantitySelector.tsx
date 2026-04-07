export function QuantitySelector({
  value,
  onChange,
}: {
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm font-medium text-walmart-gray-700">Qty:</span>
      <button
        onClick={() => onChange(Math.max(1, value - 1))}
        disabled={value <= 1}
        aria-label="Decrease quantity"
        className="w-8 h-8 rounded-full border border-walmart-gray-300 flex items-center justify-center text-lg hover:bg-walmart-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        -
      </button>
      <span className="w-8 text-center font-semibold">{value}</span>
      <button
        onClick={() => onChange(value + 1)}
        aria-label="Increase quantity"
        className="w-8 h-8 rounded-full border border-walmart-gray-300 flex items-center justify-center text-lg hover:bg-walmart-gray-50"
      >
        +
      </button>
    </div>
  );
}
