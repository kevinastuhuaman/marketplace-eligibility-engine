import { ScenarioWalkthrough } from "../components/scenarios/ScenarioWalkthrough";

export function ScenarioWalkthroughPage() {
  return (
    <div className="max-w-screen-xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-walmart-gray-900">Scenario Walkthrough</h1>
      <p className="mt-2 text-sm text-walmart-gray-500">
        A guided pass through the expanded transactability story.
      </p>
      <div className="mt-6">
        <ScenarioWalkthrough />
      </div>
    </div>
  );
}
