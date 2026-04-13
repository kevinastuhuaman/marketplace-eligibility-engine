export function ScenarioNarrationPanel({
  title,
  narration,
  whatItProves,
}: {
  title: string;
  narration?: string;
  whatItProves: string;
}) {
  return (
    <div className="rounded-xl border border-walmart-gray-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-walmart-blue">
        Scenario Narrative
      </p>
      <h2 className="mt-1 text-lg font-semibold text-walmart-gray-900">{title}</h2>
      <p className="mt-2 text-sm text-walmart-gray-600">{narration ?? whatItProves}</p>
      <p className="mt-2 text-xs uppercase tracking-wide text-walmart-gray-500">
        {whatItProves}
      </p>
    </div>
  );
}
