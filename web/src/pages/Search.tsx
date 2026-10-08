import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import type { RecItem } from "../api/types";
import MovieGrid from "../components/card/MovieGrid";

export default function Search() {
  const q = useSearchParams()[0].get("q") ?? "";
  const res = useQuery({ queryKey: ["search", q], queryFn: () => api<{ items: RecItem[] }>(`/search?q=${encodeURIComponent(q)}`), enabled: !!q });
  return (
    <div className="mx-auto max-w-[1800px] px-4 pt-24 md:px-10">
      <h1 className="font-display text-3xl font-extrabold">Results for "{q}"</h1>
      <div className="mt-6">
        {res.data && (res.data.items.length ? <MovieGrid items={res.data.items} source="search" personal={false} /> : <p className="text-muted">No films match.</p>)}
      </div>
    </div>
  );
}