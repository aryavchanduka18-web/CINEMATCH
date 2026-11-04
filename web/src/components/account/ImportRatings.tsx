import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import { send } from "../../api/client";
import { errorText } from "../../pages/Auth";

type ImportResult = {
  source: "letterboxd" | "imdb";
  rows: number;
  imported: number;
  already_rated: number;
  not_found: number;
  not_found_examples: string[];
};

const MAX_BYTES = 4_000_000;

/** Upload a Letterboxd or IMDb ratings.csv. The browser reads the file; only matched ratings are saved. */
export function ImportRatings() {
  const input = useRef<HTMLInputElement>(null);
  const qc = useQueryClient();
  const go = useMutation({
    mutationFn: async (file: File) => {
      if (file.size > MAX_BYTES) throw new Error("That file is too big. Upload ratings.csv, not the whole export.");
      return send<ImportResult>("POST", "/me/import", { csv: await file.text() });
    },
    onSuccess: () => qc.invalidateQueries(),
  });
  const r = go.data;
  return (
    <div className="space-y-3 text-sm">
      <p className="text-white/80">
        Already rate films elsewhere? Bring them in and your recommendations start from your real taste.
      </p>
      <ul className="space-y-1 text-xs text-muted">
        <li><span className="text-white/85">Letterboxd:</span> Settings, Data, Export your data. Unzip it and pick <code>ratings.csv</code>.</li>
        <li><span className="text-white/85">IMDb:</span> Your Ratings, the three-dot menu, Export. Pick the downloaded <code>.csv</code>.</li>
      </ul>
      <input ref={input} type="file" accept=".csv,text/csv" className="hidden" aria-label="Ratings file"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) go.mutate(f); e.target.value = ""; }} />
      <button className="rounded-md bg-white px-4 py-2 text-sm font-semibold text-black disabled:opacity-60"
        disabled={go.isPending} onClick={() => input.current?.click()}>
        {go.isPending ? "Importing..." : "Choose ratings file"}
      </button>
      {go.isError && (
        <p role="alert" className="rounded-md bg-red-500/10 px-3 py-2 text-red-300">
          {go.error instanceof Error && !("status" in go.error) ? go.error.message : errorText(go.error)}
        </p>
      )}
      {r && (
        <div role="status" className="rounded-md bg-emerald-500/10 px-3 py-2 text-emerald-100">
          <p>
            Imported <b>{r.imported}</b> of {r.rows} {r.source === "imdb" ? "IMDb" : "Letterboxd"} ratings.
            {r.already_rated > 0 && <> {r.already_rated} you had already rated here were left as they were.</>}
          </p>
          {r.not_found > 0 && (
            <p className="mt-1 text-xs text-emerald-100/80">
              {r.not_found} films are not in the FlickRaven catalog{r.not_found_examples.length > 0 && <>, for example {r.not_found_examples.slice(0, 4).join(", ")}</>}.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
