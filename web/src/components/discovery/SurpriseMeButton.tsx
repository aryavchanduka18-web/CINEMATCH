import { useMutation } from "@tanstack/react-query";
import { api } from "../../api/client";
import type { RecItem } from "../../api/types";
import { useUI } from "../layout/ui";

export default function SurpriseMeButton() {
  const { openQuickView, notify } = useUI();
  const go = useMutation({
    mutationFn: () => api<{ item: RecItem | null; message?: string }>("/recs/surprise"),
    onSuccess: (r) => (r.item ? openQuickView(r.item) : notify(r.message ?? "Nothing to surprise you with yet")),
  });
  return (
    <button onClick={() => go.mutate()} disabled={go.isPending}
      className="rounded-full border border-white/20 px-4 py-2 text-sm hover:border-white/50 disabled:opacity-60">
      {go.isPending ? "Picking…" : "Surprise Me"}
    </button>
  );
}