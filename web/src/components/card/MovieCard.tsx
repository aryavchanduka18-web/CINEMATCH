import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useLayoutEffect, useRef, useState, type CSSProperties, type RefObject } from "react";
import { createPortal } from "react-dom";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import type { MovieDetail, RecItem } from "../../api/types";
import { useCanHover } from "../../hooks/useCanHover";
import { agreementLabel } from "../../lib/confidence";
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
      {personal && item.match_pct != null && agreementLabel(item.agreement) && (
        <span className="rounded border border-white/15 px-1.5 text-[11px] text-white/70" title={`Model agreement ${item.agreement}%`}>
          {agreementLabel(item.agreement)} agreement
        </span>
      )}
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
  const card = useRef<HTMLDivElement>(null);
  const body = useRef<HTMLDivElement>(null);
  const m = item.movie;
  const close = () => {
    window.clearTimeout(timer.current);
    setHover(false);
  };
  // While the details are open, the wheel over the card or the details scrolls only the details: never the
  // page, never the rail. A page scroll from elsewhere (keyboard, scrollbar) closes them.
  useEffect(() => {
    if (!hover) return;
    const el = card.current;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (body.current) body.current.scrollTop += e.deltaY;
    };
    el?.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("scroll", close, { passive: true });
    window.addEventListener("resize", close);
    return () => {
      el?.removeEventListener("wheel", onWheel);
      window.removeEventListener("scroll", close);
      window.removeEventListener("resize", close);
    };
  }, [hover]);
  const open = () => navigate(`/movie/${m.id}`, { state: { source, position } });

  return (
    <motion.div
      ref={card}
      className="relative"
      onMouseEnter={() => {
        if (!canHover) return;
        window.clearTimeout(timer.current);
        timer.current = window.setTimeout(() => setHover(true), 280); // hover intent: no flicker across a rail
      }}
      onMouseLeave={() => {
        // A short grace period lets the pointer move from the card onto the details below it.
        window.clearTimeout(timer.current);
        timer.current = window.setTimeout(() => setHover(false), 120);
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
      {createPortal(
        <AnimatePresence>
          {hover && card.current && (
            <HoverDetails item={item} source={source} anchor={card.current} body={body}
              onEnter={() => window.clearTimeout(timer.current)} onLeave={close} />
          )}
        </AnimatePresence>,
        document.body,
      )}
    </motion.div>
  );
}

/** The details under a hovered card, rendered in a portal on top of everything (no rail can clip it), placed
 *  under the card and never taller than the space left on screen. The mouse wheel scrolls only its body. */
function HoverDetails({ item, source, anchor, body, onEnter, onLeave }: {
  item: RecItem; source: string; anchor: HTMLElement; body: RefObject<HTMLDivElement | null>;
  onEnter: () => void; onLeave: () => void;
}) {
  const { openQuickView, openWhy } = useUI();
  const m = item.movie;
  const panel = useRef<HTMLDivElement>(null);
  const detail = useQuery({ queryKey: ["movie", m.id], queryFn: () => api<MovieDetail>(`/movies/${m.id}`), staleTime: 60_000 });
  const [place, setPlace] = useState(() => placement(anchor));
  // Follow the card: re-measure on any scroll (page or rail) and on resize.
  useLayoutEffect(() => {
    const update = () => setPlace(placement(anchor));
    window.addEventListener("scroll", update, { capture: true, passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update, { capture: true });
      window.removeEventListener("resize", update);
    };
  }, [anchor]);
  useEffect(() => {
    const el = panel.current;
    if (!el) return;
    // A native, non-passive listener: React's onWheel cannot cancel the page scroll.
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (body.current) body.current.scrollTop += e.deltaY;
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [body]);
  const d = detail.data;
  return (
    <motion.div
      ref={panel}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.16 }}
      style={place.style}
      className={`z-[45] bg-surface shadow-2xl ring-1 ring-white/10 ${place.above ? "rounded-t-md" : "rounded-b-md"}`}
      data-testid="hover-details"
    >
      <div className="flex items-center justify-between p-3 pb-2">
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
      <div ref={body} style={{ maxHeight: place.maxBody }} className="overflow-y-auto overscroll-contain px-3 pb-3"
        tabIndex={0} aria-label={`${m.title} details`}>
        <div className="text-xs text-muted">
          {[m.genres.slice(0, 3).join(" · "), d?.runtime ? `${d.runtime} min` : null, d?.certification].filter(Boolean).join(" · ")}
        </div>
        {item.reasons[0] && (
          <p className="mt-1.5 text-xs text-white/75">
            {item.reasons[0].text}
            {item.match_pct != null && (
              <button onClick={() => openWhy(m.id)} className="ml-2 font-medium text-white underline underline-offset-2">Why?</button>
            )}
          </p>
        )}
        {(d?.overview ?? m.overview_short) && <p className="mt-2 text-xs leading-relaxed text-white/80">{d?.overview ?? m.overview_short}</p>}
        {d && d.directors.length > 0 && (
          <p className="mt-2 text-xs text-muted">Directed by <span className="text-white/85">{d.directors.map((x) => x.name).join(", ")}</span></p>
        )}
        {d && d.cast.length > 0 && (
          <div className="mt-2 flex gap-2">
            {d.cast.slice(0, 5).map((c) => (
              <Link key={c.id} to={`/person/${c.id}`} className="group w-12 shrink-0 text-center" title={c.name}>
                <div className="mx-auto h-10 w-10 overflow-hidden rounded-full bg-surface-2 ring-1 ring-white/10 group-hover:ring-white/40">
                  {c.profile_path && <img src={tmdbImage(c.profile_path, "w300")} alt="" loading="lazy" className="h-full w-full object-cover" />}
                </div>
                <div className="mt-1 truncate text-[10px] leading-tight text-white/70">{c.name}</div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

/** Under the card when there is room; above it when the card sits near the bottom of the screen. */
function placement(anchor: HTMLElement): { style: CSSProperties; maxBody: number; above: boolean } {
  const r = anchor.getBoundingClientRect();
  const below = window.innerHeight - r.bottom;
  const above = below < 240 && r.top > below;
  const room = (above ? r.top : below) - 90;
  const base: CSSProperties = { position: "fixed", left: r.left, width: r.width };
  return {
    above,
    maxBody: Math.max(120, Math.min(260, room)),
    style: above ? { ...base, bottom: window.innerHeight - r.top - 4 } : { ...base, top: r.bottom - 4 },
  };
}

export function Chevron() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}