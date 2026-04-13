import { useUiStore } from "../../store/ui-store";

export function ThemeToggle() {
  const theme = useUiStore((state) => state.theme);
  const toggleTheme = useUiStore((state) => state.toggleTheme);

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="rounded-full border border-white/25 px-3 py-1 text-xs font-semibold text-white"
    >
      {theme === "light" ? "Night" : "Light"}
    </button>
  );
}
