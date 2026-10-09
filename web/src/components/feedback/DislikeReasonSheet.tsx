import { useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { send } from "../../api/client";
import { useUI } from "../layout/ui";

const REASONS: [string, string][] = [
  ["genre", "Not into this genre"], ["long", "Too long"], ["language", "Not my language"],
  ["seen", "Already seen it"], ["similar", "Too similar to others"], ["none", "Just not for me"],
];

/** After a dislike: one tap to say why. Each answer changes something real (see POST /feedback/dislike-reason). */
export default function DislikeReasonSheet() {
  const { dislikeId, askDislikeReason, notify } = useUI();
  const qc = useQueryClient();
  const choose = async (reason: string) => {
    if (dislikeId == null) return;
    const id = dislikeId;
    askDislikeReason(null);
    const res = await send<{ message: string }>("POST", "/feedback/dislike-reason", { movie_id: id, reason }).catch(() => null);
    notify(res?.message ?? "Thanks, noted.");
    for (const k of ["home", "taste", "movie", "explain", "discover", "collections"]) qc.invalidateQueries({ queryKey: [k] });
  };
  return (
    <AnimatePresence>
      {dislikeId != null && (
        <motion.div role="dialog" aria-label="Why not for you?" initial={{ y: 40, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
          exit={{ y: 40, opacity: 0 }} transition={{ duration: 0.18 }}
          className="fixed inset-x-3 bottom-24 z-50 mx-auto max-w-md rounded-2xl bg-surface p-4 shadow-2xl ring-1 ring-white/10 md:bottom-8">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm font-semibold">Hidden. What was not for you?</p>
            <button onClick={() => askDislikeReason(null)} className="text-xs text-muted hover:text-white">Skip</button>
          </div>
          <div className="flex flex-wrap gap-2">
            {REASONS.map(([k, l]) => (
              <button key={k} onClick={() => choose(k)} className="rounded-full border border-white/20 px-3 py-1.5 text-sm hover:border-white/60">{l}</button>
            ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
