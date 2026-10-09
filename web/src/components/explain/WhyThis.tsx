import { Link } from "react-router-dom";
import type { Reason } from "../../api/types";

/** "Why you're seeing this": only reasons whose source gave >= 20% of the score (computed server-side). */
export default function WhyThis({ reasons, compact = false }: { reasons?: Reason[]; compact?: boolean }) {
  if (!reasons?.length) return null;
  return (
    <div className={compact ? "" : "rounded-lg border border-white/10 bg-surface p-4"}>
      {!compact && <h3 className="mb-2 text-sm font-semibold">Why you're seeing this</h3>}
      <ul className="space-y-1.5 text-sm text-white/85">
        {reasons.map((r, i) => (
          <li key={r.code + r.text} className="flex items-baseline gap-2">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
            <span>
              {r.anchor_movie_id ? (
                <Link to={`/movie/${r.anchor_movie_id}`} className="underline decoration-white/30 underline-offset-2 hover:decoration-white">
                  {r.text}
                </Link>
              ) : (
                r.text
              )}
              {!compact && r.share > 0 && (
                <span className="ml-2 text-xs text-muted">
                  {i === 0 && reasons.length > 1 ? "biggest reason, " : ""}about {Math.round(r.share * 100)}% of your match
                </span>
              )}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}