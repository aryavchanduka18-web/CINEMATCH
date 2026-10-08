import type { Mode } from "../../api/types";

const MODES: { value: Mode; label: string; hint: string }[] = [
  { value: "familiar", label: "Familiar", hint: "Close to what you already love" },
  { value: "balanced", label: "Balanced", hint: "A mix of safe bets and new finds" },
  { value: "discover", label: "Discover", hint: "More variety, other languages, lesser-known films" },
];

/** Familiar <-> Balanced <-> Discover. It really changes the MMR reranking (spec 6.8). */
export default function DiscoveryModeControl({ value, onChange }: { value: Mode; onChange: (m: Mode) => void }) {
  const current = MODES.find((m) => m.value === value) ?? MODES[1];
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div role="radiogroup" aria-label="Discovery Mode" className="inline-flex rounded-full border border-white/15 bg-surface p-1">
        {MODES.map((m) => (
          <button
            key={m.value}
            role="radio"
            aria-checked={value === m.value}
            onClick={() => onChange(m.value)}
            className={`rounded-full px-4 py-1.5 text-sm transition-colors duration-150 ${
              value === m.value ? "bg-white font-medium text-black" : "text-white/80 hover:bg-white/10"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>
      <span className="text-sm text-muted">{current.hint}</span>
    </div>
  );
}