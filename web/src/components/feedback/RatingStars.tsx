import { useState } from "react";

type Props = { value: number | null; onChange: (rating: number | null) => void; size?: number };

/** 5 stars with half steps = the CineMatch 1-10 scale (half a star = 1 point). Click again to clear. */
export default function RatingStars({ value, onChange, size = 28 }: Props) {
  const [hover, setHover] = useState<number | null>(null);
  const shown = hover ?? value ?? 0;
  return (
    <div className="flex items-center gap-3">
      <div className="flex" role="radiogroup" aria-label="Your rating" onMouseLeave={() => setHover(null)}>
        {[1, 2, 3, 4, 5].map((star) => (
          <div key={star} className="relative" style={{ width: size, height: size }}>
            <StarShape fill={Math.max(0, Math.min(1, (shown - (star - 1) * 2) / 2))} size={size} />
            {[star * 2 - 1, star * 2].map((v, half) => (
              <button
                key={v}
                role="radio"
                aria-checked={value === v}
                aria-label={`${v / 2} stars (${v}/10)`}
                className="absolute top-0 h-full w-1/2"
                style={{ left: half ? "50%" : 0 }}
                onMouseEnter={() => setHover(v)}
                onFocus={() => setHover(v)}
                onBlur={() => setHover(null)}
                onClick={() => onChange(value === v ? null : v)}
              />
            ))}
          </div>
        ))}
      </div>
      <span className="text-sm tabular-nums text-muted">{shown ? `${shown}/10` : "Rate it"}</span>
    </div>
  );
}

function StarShape({ fill, size }: { fill: number; size: number }) {
  const id = `s${Math.round(fill * 100)}`;
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} aria-hidden>
      <defs>
        <linearGradient id={id}>
          <stop offset={`${fill * 100}%`} stopColor="var(--cm-accent)" />
          <stop offset={`${fill * 100}%`} stopColor="transparent" />
        </linearGradient>
      </defs>
      <path
        d="M12 2.8l2.8 5.9 6.4.8-4.7 4.4 1.2 6.4L12 17.2l-5.7 3.1 1.2-6.4-4.7-4.4 6.4-.8z"
        fill={`url(#${id})`}
        stroke={fill > 0 ? "var(--cm-accent)" : "#ffffff55"}
        strokeWidth="1.3"
        strokeLinejoin="round"
      />
    </svg>
  );
}