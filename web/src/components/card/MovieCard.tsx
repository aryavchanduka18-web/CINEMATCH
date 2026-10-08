import { AnimatePresence, motion } from "framer-motion";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { RecItem } from "../../api/types";
import { useCanHover } from "../../hooks/useCanHover";
import { backdropSrcSet, tmdbImage } from "../../lib/tmdb";
import { languageName } from "../../lib/format";
import ActionButtons from "../feedback/ActionButtons";
import { useUI } from "../layout/ui";

type Props = { item: RecItem; source: string; position: number; personal?: boolean };

export function CardArtwork({ item, eager = false }: { item: RecItem; eager?: boolean }) {
  const m = item.movie;
  const img = m.backdrop ? tmdbImage(m.backdrop, "w780") : tmdbImage(m.poster, "w500");
  return (
    <div className="relative aspect-video overflow-hidden rounded-md bg-surface-2">
      {img && (
        <img
          src={img}
          srcSet={m.backdrop ? backdropSrcSet(m.backdrop) : undefined}
          sizes="(min-width: 1280px) 40vw, (min-width: 768px) 48vw, 80vw"
          alt=""
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          className={`h-full w-full object-cover ${m.backdrop ? "" : "scale-110 blur-sm"}`}
        />
      )}
      <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/25 to-transparent" />
      <div className="absolute inset-x-0 bottom-0 p-3 md:p-4">
        {m.logo ? (
          <img src={tmdbImage(m.logo, "w500")} alt={m.title} className="max-h-12 max-w-[60%] object-contain object-left drop-shadow md:max-h-16" loading="lazy" />
        ) : (
          <h3 className="font-display text-lg font-bold leading-tight drop-shadow md:text-xl">{m.title}</h3>
        )}
      </div>
    </div>
  );
}

export function CardMeta({ item, personal }: { item: RecItem; personal?: boolean }) {
  const m = item.movie;
  return (
    <div className="mt-2 flex items-center gap-2 text-[13px] text-muted">
      {personal && item.match_pct != null && <span className="font-semibold text-accent">{item.match_pct}% match</span>}
      {m.year && <span>{m.year}</span>}
      {m.community_rating != null && <span>★ {m.community_rating.toFixed(1)}</span>}
      {m.language && <span>{languageName(m.language)}</span>}
    </div>
  );
}

export default function MovieCard({ item, source, position, personal = true }: Props) {
  const canHover = useCanHover();
  const navigate = useNavigate();
  const { openQuickView } = useUI();
  const [hover, setHover] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  const m = item.movie;
  const open = () => navigate(`/movie/${m.id}`, { state: { source, position } });

  return (
    <motion.div
      className="relative"
      onMouseEnter={() => {
        if (!canHover) return;
        timer.current = window.setTimeout(() => setHover(true), 280); // hover intent: no flicker across a rail
      }}
      onMouseLeave={() => {
        window.clearTimeout(timer.current);
        setHover(false);
      }}
      animate={hover ? { scale: 1.05, y: -4 } : { scale: 1, y: 0 }}
      transition={{ duration: 0.2, ease: [0.2, 0.7, 0.2, 1] }}
      style={{ zIndex: hover ? 20 : 1 }}
    >
      <button onClick={open} className="block w-full text-left" aria-label={`${m.title}${m.year ? ` (${m.year})` : ""}`}>
        <CardArtwork item={item} />
      </button>
      <div className="flex items-start justify-between gap-2">
        <CardMeta item={item} personal={personal} />
        {!canHover && (
          <button
            onClick={() => openQuickView(item)}
            className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-full border border-white/25 text-white"
            aria-label={`Quick view ${m.title}`}
          >
            <Chevron />
          </button>
        )}
      </div>
      <AnimatePresence>
        {hover && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.16 }}
            className="absolute inset-x-0 top-full z-30 -mt-1 rounded-b-md bg-surface p-3 shadow-2xl ring-1 ring-white/10"
          >
            <div className="flex items-center justify-between">
              <ActionButtons movieId={m.id} state={item.user_state} source={source} />
              <button
                onClick={() => openQuickView(item)}
                className="grid h-8 w-8 place-items-center rounded-full border border-white/30 text-white hover:border-white"
                aria-label={`Quick view ${m.title}`}
                title="Quick View"
              >
                <Chevron />
              </button>
            </div>
            <div className="mt-2 text-xs text-muted">{m.genres.slice(0, 3).join(" · ")}</div>
            {m.overview_short && <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-white/80">{m.overview_short}</p>}
            {item.reasons[0] && <p className="mt-1.5 text-xs text-white/60">{item.reasons[0].text}</p>}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function Chevron() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}