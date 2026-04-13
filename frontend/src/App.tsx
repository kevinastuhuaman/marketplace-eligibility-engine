import { Routes, Route } from "react-router-dom";
import { Header } from "./components/layout/Header";
import { ScenarioStrip } from "./components/scenarios/ScenarioStrip";
import { SplitPanel } from "./components/layout/SplitPanel";
import { HomePage } from "./pages/HomePage";
import { ProductPage } from "./pages/ProductPage";
import { ComparePage } from "./pages/ComparePage";
import { ScenarioWalkthroughPage } from "./pages/ScenarioWalkthroughPage";
import { PrintScenarioPage } from "./pages/PrintScenarioPage";
import { useUiStore } from "./store/ui-store";

export default function App() {
  const theme = useUiStore((state) => state.theme);

  return (
    <div className={theme === "night" ? "min-h-screen bg-slate-950" : "min-h-screen bg-white"}>
      <Header />
      <ScenarioStrip />
      <SplitPanel>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/product/:id" element={<ProductPage />} />
          <Route path="/compare/:id" element={<ComparePage />} />
          <Route path="/scenarios/walkthrough" element={<ScenarioWalkthroughPage />} />
          <Route path="/print/scenario/:scenarioId" element={<PrintScenarioPage />} />
        </Routes>
      </SplitPanel>
    </div>
  );
}
