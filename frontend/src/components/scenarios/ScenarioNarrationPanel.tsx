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
    <div className="rounded-xl border border-brand-gray-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-brand-blue">
        Scenario Narrative
      </p>
      <h2 className="mt-1 text-lg font-semibold text-brand-gray-900">{title}</h2>
      <p className="mt-2 text-sm text-brand-gray-600">{narration ?? whatItProves}</p>
      <p className="mt-2 text-xs uppercase tracking-wide text-brand-gray-500">
        {whatItProves}
      </p>
    </div>
  );
}
