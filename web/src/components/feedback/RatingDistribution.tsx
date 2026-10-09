/** Ratings on the 1-10 scale, one bar per value (MovieLens + CineMatch ratings). */
export default function RatingDistribution({ hist }: { hist: number[] }) {
  const max = Math.max(1, ...hist);
  const total = hist.reduce((a, b) => a + b, 0);
  if (!total) return <p className="text-sm text-muted">No ratings yet.</p>;
  return (
    <div>
      <div className="flex h-24 items-end gap-1.5" role="img" aria-label="Rating distribution from 1 to 10">
        {hist.map((n, i) => (
          <div key={i} className="flex h-full flex-1 flex-col items-center justify-end gap-1">
            <div className="w-full rounded-sm bg-white/70" style={{ height: `${(n / max) * 100}%`, minHeight: n ? 2 : 0 }} title={`${i + 1}/10: ${n}`} />
          </div>
        ))}
      </div>
      <div className="mt-1 flex gap-1.5 text-[11px] text-muted">
        {hist.map((_, i) => (
          <span key={i} className="flex-1 text-center tabular-nums">{i + 1}</span>
        ))}
      </div>
      <p className="mt-2 text-xs text-muted">{total.toLocaleString()} ratings</p>
    </div>
  );
}