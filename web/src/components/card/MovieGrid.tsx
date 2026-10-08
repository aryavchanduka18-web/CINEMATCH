import type { RecItem } from "../../api/types";
import MovieCard from "./MovieCard";

export default function MovieGrid({ items, source, personal = true }: { items: RecItem[]; source: string; personal?: boolean }) {
  return (
    <div className="grid grid-cols-1 gap-x-4 gap-y-8 pb-20 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
      {items.map((it, i) => (
        <MovieCard key={it.movie.id} item={it} source={source} position={i} personal={personal} />
      ))}
    </div>
  );
}