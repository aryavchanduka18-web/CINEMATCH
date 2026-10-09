import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, send } from "../../api/client";

type Tuning = { adventurous: number; hidden: number; international: number; length: number };

const SLIDERS: { key: keyof Tuning; left: string; right: string; knob: string }[] = [
  { key: "adventurous", left: "More familiar", right: "More adventurous", knob: "MMR diversity (lambda)" },
  { key: "hidden", left: "Popular", right: "Hidden gems", knob: "Novelty weight" },
  { key: "international", left: "Indian and English", right: "International", knob: "Language boost" },
  { key: "length", left: "Shorter", right: "Longer", knob: "Runtime preference" },
];
const NEUTRAL: Tuning = { adventurous: 50, hidden: 50, international: 50, length: 50 };

/** Tune your recommendations: four sliders the engine re-ranks with (engine Tuning, PUT /me/tuning).
 *  All at the middle gives exactly the untuned lists. */
export default function TunePanel({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const saved = useQuery({ queryKey: ["tuning"], queryFn: () => api<Tuning>("/me/tuning") });
  const [t, setT] = useState<Tuning>(NEUTRAL);
  useEffect(() => {
    if (saved.data) setT(saved.data);
  }, [saved.data]);
  const apply = useMutation({
    mutationFn: (v: Tuning) => send<Tuning>("PUT", "/me/tuning", v),
    onSuccess: () => {
      for (const k of ["tuning", "home", "discover"]) qc.invalidateQueries({ queryKey: [k] });
      onClose();
    },
  });
  return (
    <section aria-label="Tune your recommendations" className="rounded-2xl border border-white/10 bg-surface p-5 md:p-6">
      <div className="mb-5 flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h2 className="font-display text-lg font-bold">Tune your recommendations</h2>
          <p className="text-sm text-muted">You set the objective. The engine re-ranks Top Picks, the hero and Discover with it.</p>
        </div>
        <button onClick={() => setT(NEUTRAL)} className="text-sm text-muted hover:text-white">Reset</button>
      </div>
      <div className="grid gap-x-10 gap-y-6 md:grid-cols-2">
        {SLIDERS.map((s) => (
          <label key={s.key} className="block">
            <div className="mb-2 flex justify-between text-sm text-white/80"><span>{s.left}</span><span>{s.right}</span></div>
            <input type="range" min={0} max={100} step={5} value={t[s.key]} aria-label={`${s.left} to ${s.right}`}
              onChange={(e) => setT({ ...t, [s.key]: Number(e.target.value) })} className="w-full accent-[var(--color-accent)]" />
            <div className="mt-1 text-[11px] text-muted">Changes: {s.knob}</div>
          </label>
        ))}
      </div>
      <div className="mt-6 flex gap-3">
        <button onClick={() => apply.mutate(t)} className="rounded-md bg-white px-5 py-2 text-sm font-semibold text-black">
          {apply.isPending ? "Applying…" : "Apply"}
        </button>
        <button onClick={onClose} className="rounded-md px-4 py-2 text-sm text-white/80 ring-1 ring-white/20 hover:bg-white/10">Cancel</button>
      </div>
    </section>
  );
}
