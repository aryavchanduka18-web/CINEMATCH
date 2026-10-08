import { useEffect, useRef, useState } from "react";
import type { RecItem } from "../../api/types";
import MovieCard from "../card/MovieCard";

type Props = { title: string; items: RecItem[]; source: string; personal?: boolean };

/** One horizontal rail. Card width gives about 2-3 large cards on desktop with the next one peeking,
 *  about 2 on tablet and 1-1.5 on phones (spec 8.4). Vertical padding keeps hovered cards unclipped. */
export default function Rail({ title, items, source, personal = true }: Props) {
  const scroller = useRef<HTMLDivElement>(null);
  const [edge, setEdge] = useState({ start: true, end: false });

  const update = () => {
    const el = scroller.current;
    if (!el) return;
    setEdge({ start: el.scrollLeft < 8, end: el.scrollLeft + el.clientWidth >= el.scrollWidth - 8 });
  };
  useEffect(update, [items.length]);

  const scrollBy = (dir: number) => {
    const el = scroller.current;
    if (el) el.scrollBy({ left: dir * el.clientWidth * 0.85, behavior: "smooth" });
  };

  if (!items.length) return null;
  return (
    <section className="group/rail relative" aria-label={title}>
      <h2 className="mb-1 px-4 font-display text-lg font-bold md:px-10 md:text-xl">{title}</h2>
      <div
        ref={scroller}
        onScroll={update}
        className="no-scrollbar flex snap-x snap-mandatory gap-3 overflow-x-auto scroll-px-4 px-4 pb-28 pt-3 -mb-24 md:scroll-px-10 md:gap-4 md:px-10"
      >
        {items.map((it, i) => (
          <div key={it.movie.id} className="w-[78vw] shrink-0 snap-start sm:w-[46vw] lg:w-[38vw] xl:w-[34vw] 2xl:w-[30vw]">
            <MovieCard item={it} source={source} position={i} personal={personal} />
          </div>
        ))}
      </div>
      <RailArrow side="left" hidden={edge.start} onClick={() => scrollBy(-1)} />
      <RailArrow side="right" hidden={edge.end} onClick={() => scrollBy(1)} />
    </section>
  );
}

function RailArrow({ side, hidden, onClick }: { side: "left" | "right"; hidden: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      aria-label={side === "left" ? "Scroll left" : "Scroll right"}
      tabIndex={hidden ? -1 : 0}
      className={`absolute top-[calc(50%-3rem)] z-30 hidden h-12 w-12 place-items-center rounded-full border border-white/25 bg-black/35 text-white opacity-0 backdrop-blur-md transition-opacity duration-200 hover:bg-black/55 md:grid ${
        hidden ? "pointer-events-none" : "group-hover/rail:opacity-100 focus:opacity-100"
      } ${side === "left" ? "left-3" : "right-3"}`}
    >
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
        <path d={side === "left" ? "m15 6-6 6 6 6" : "m9 6 6 6-6 6"} />
      </svg>
    </button>
  );
}