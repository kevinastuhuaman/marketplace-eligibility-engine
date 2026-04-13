import { Link } from "react-router-dom";
import { LocationSelector } from "../customer/LocationSelector";
import { useEvaluationStore } from "../../store/evaluation-store";
import { ThemeToggle } from "./ThemeToggle";

export function Header() {
  const { testerMode, toggleTesterMode } = useEvaluationStore();

  return (
    <header className="bg-brand-blue text-white">
      <div className="max-w-screen-2xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <svg viewBox="0 0 24 24" className="w-7 h-7" fill="none" stroke="#FFC220" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <path d="M9 12l2 2 4-4" stroke="#FFC220" strokeWidth="2" />
          </svg>
          <span className="text-lg font-bold tracking-tight">Marketplace</span>
        </Link>

        <div className="flex items-center gap-4">
          <Link to="/scenarios/walkthrough" className="text-xs font-semibold text-blue-100">
            Walkthrough
          </Link>

          <a href="/industry-landscape.html" className="text-xs font-semibold text-blue-100">
            Industry Landscape
          </a>

          <LocationSelector />

          <ThemeToggle />

          <div className="flex items-center gap-2 ml-4">
            <span className="text-xs text-blue-200">Customer</span>
            <button
              type="button"
              role="switch"
              aria-checked={testerMode}
              aria-label="Toggle tester mode"
              onClick={toggleTesterMode}
              className="relative w-11 h-6 rounded-full transition-colors cursor-pointer"
              style={{ backgroundColor: testerMode ? "#FFC220" : "rgba(255,255,255,0.3)" }}
            >
              <div
                className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform"
                style={{ transform: testerMode ? "translateX(22px)" : "translateX(2px)" }}
              />
            </button>
            <span className="text-xs text-blue-200">Tester</span>
          </div>
        </div>
      </div>
    </header>
  );
}
