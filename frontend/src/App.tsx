import { Routes, Route } from "react-router-dom";
import { Header } from "./components/layout/Header";
import { ScenarioStrip } from "./components/scenarios/ScenarioStrip";
import { SplitPanel } from "./components/layout/SplitPanel";
import { HomePage } from "./pages/HomePage";
import { ProductPage } from "./pages/ProductPage";

export default function App() {
  return (
    <div className="min-h-screen bg-white">
      <Header />
      <ScenarioStrip />
      <SplitPanel>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/product/:id" element={<ProductPage />} />
        </Routes>
      </SplitPanel>
    </div>
  );
}
