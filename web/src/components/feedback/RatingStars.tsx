import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useState, type KeyboardEvent } from "react";

type Props = { value: number | null; onChange: (rating: number | null) => void; size?: number };

/** 5 stars with half steps = the CineMatch 1-10 scale (half a star = 1 point).
 *  Tap or click any star to set or change the rating at once; "Clear" removes it. Keyboard: the arrow keys
 *  move by one point, Home/End jump to 1 and 10, Delete clears. */
export default function RatingStars({ value: server, onChange, size = 30 }: Props) {
  const reduce = useReducedMotion();
  const [value, setValue] = useState(server);          // optimistic: shows the new rating immediately
  useEffect(() => setValue(server), [server]);
  const [hover, setHover] = useState<number | null>(null);
  const shown = hover ?? value ?? 0;
  const set = (v: number | null) => {
    if (v === value) return;
    setValue(v);
    onChange(v);
  };
  const onKey = (e: KeyboardEvent) => {
    const cur = value ?? 0;
    const next = ({ ArrowRight: cur + 1, ArrowUp: cur + 1, ArrowLeft: cur - 1, ArrowDown: cur - 1, Home: 1, End: 10 } as Record<string, number>)[e.key];
    if (next !== undefined) {
      e.preventDefault();
      set(Math.max(1, Math.min(10, next)));
    } else if (e.key === "Delete" || e.key === "Backspace") {
      e.preventDefault();
      set(null);
    }
  };
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
      <div className="flex rounded-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent" role="slider"
        tabIndex={0} aria-label="Your rating, 1 to 10" aria-valuemin={1} aria-valuemax={10} aria-valuenow={value ?? undefined}
        aria-valuetext={value ? `${value} out of 10` : "Not rated"} onKeyDown={onKey} onMouseLeave={() => setHover(null)}>
        {[1, 2, 3, 4, 5].map((star) => (
          <div key={star} className="relative" style={{ width: size, height: size }}>
            <StarShape fill={Math.max(0, Math.min(1, (shown - (star - 1) * 2) / 2))} size={size} preview={hover != null} />
            {[star * 2 - 1, star * 2].map((v, half) => (
              <button key={v} type="button" tabIndex={-1} aria-hidden
                className="absolute top-0 h-full w-1/2" style={{ left: half ? "50%" : 0 }}
                onMouseEnter={() => setHover(v)} onClick={() => set(v)} />
            ))}
          </div>
        ))}
      </div>
      <motion.span key={value ?? 0} initial={reduce || !value ? false : { scale: 1.25, color: "#E0263F" }}
        animate={{ scale: 1, color: "#d4d4d4" }} transition={{ duration: 0.35 }} className="min-w-[7rem] text-sm tabular-nums">
        {hover != null ? `Set ${hover}/10` : value ? `Your rating ${value}/10` : "Rate it"}
      </motion.span>
      {value != null && (
        <button type="button" onClick={() => set(null)}
          className="rounded-full border border-white/20 px-2.5 py-0.5 text-xs text-white/75 hover:border-white/50 hover:text-white">
          Clear
        </button>
      )}
    </div>
  );
}

function StarShape({ fill, size, preview }: { fill: number; size: number; preview: boolean }) {
  const id = `s${Math.round(fill * 100)}${preview ? "p" : ""}`;
  const color = preview ? "#f0a0ad" : "var(--cm-accent)";
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} aria-hidden>
      <defs>
        <linearGradient id={id}>
          <stop offset={`${fill * 100}%`} stopColor={color} />
          <stop offset={`${fill * 100}%`} stopColor="transparent" />
        </linearGradient>
      </defs>
      <path
        d="M12 2.8l2.8 5.9 6.4.8-4.7 4.4 1.2 6.4L12 17.2l-5.7 3.1 1.2-6.4-4.7-4.4 6.4-.8z"
        fill={`url(#${id})`}
        stroke={fill > 0 ? color : "#ffffff55"}
        strokeWidth="1.3"
        strokeLinejoin="round"
      />
    </svg>
  );
}
