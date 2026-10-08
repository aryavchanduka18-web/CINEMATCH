// Small, plain SVG charts for the Lab: one consistent style, numbers straight from artifacts/.
type Series = { name: string; points: [number, number][]; dashed?: boolean; color: string };

export function LineChart({ series, xLabel, yLabel, width = 640, height = 300, xTicks }: {
  series: Series[]; xLabel: string; yLabel: string; width?: number; height?: number; xTicks?: number[];
}) {
  const pad = { l: 52, r: 16, t: 12, b: 40 };
  const all = series.flatMap((s) => s.points);
  if (!all.length) return null;
  const [x0, x1] = [Math.min(...all.map((p) => p[0])), Math.max(...all.map((p) => p[0]))];
  const y1 = Math.max(...all.map((p) => p[1])) * 1.1 || 1;
  const sx = (x: number) => pad.l + ((x - x0) / (x1 - x0 || 1)) * (width - pad.l - pad.r);
  const sy = (y: number) => height - pad.b - (y / y1) * (height - pad.t - pad.b);
  const ticks = xTicks ?? Array.from(new Set(all.map((p) => p[0]))).sort((a, b) => a - b);
  return (
    <figure>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" role="img" aria-label={`${yLabel} by ${xLabel}`}>
        {[0, 0.25, 0.5, 0.75, 1].map((f) => (
          <g key={f}>
            <line x1={pad.l} x2={width - pad.r} y1={sy(y1 * f)} y2={sy(y1 * f)} stroke="#ffffff14" />
            <text x={pad.l - 8} y={sy(y1 * f) + 4} textAnchor="end" fontSize="11" fill="#a7a7a7">{(y1 * f).toFixed(3)}</text>
          </g>
        ))}
        {ticks.map((t) => <text key={t} x={sx(t)} y={height - pad.b + 18} textAnchor="middle" fontSize="11" fill="#a7a7a7">{t}</text>)}
        <text x={(width + pad.l) / 2} y={height - 4} textAnchor="middle" fontSize="12" fill="#a7a7a7">{xLabel}</text>
        {series.map((s) => (
          <g key={s.name}>
            <polyline fill="none" stroke={s.color} strokeWidth="2" strokeDasharray={s.dashed ? "5 4" : undefined}
              points={s.points.map(([x, y]) => `${sx(x)},${sy(y)}`).join(" ")} />
            {s.points.map(([x, y]) => <circle key={x} cx={sx(x)} cy={sy(y)} r="3" fill={s.color} />)}
          </g>
        ))}
      </svg>
      <figcaption className="mt-2 flex flex-wrap gap-4 text-xs text-muted">
        {series.map((s) => (
          <span key={s.name} className="flex items-center gap-1.5">
            <svg width="18" height="6"><line x1="0" x2="18" y1="3" y2="3" stroke={s.color} strokeWidth="2" strokeDasharray={s.dashed ? "4 3" : undefined} /></svg>
            {s.name}
          </span>
        ))}
      </figcaption>
    </figure>
  );
}

export function ScatterChart({ points, xLabel, yLabel, marks }: {
  points: { x: number; y: number; label?: string }[]; xLabel: string; yLabel: string; marks?: { x: number; y: number; label: string }[];
}) {
  const width = 640, height = 300, pad = { l: 56, r: 16, t: 12, b: 40 };
  const xs = [...points, ...(marks ?? [])].map((p) => p.x), ys = [...points, ...(marks ?? [])].map((p) => p.y);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys) * 0.95, Math.max(...ys) * 1.05];
  const sx = (x: number) => pad.l + ((x - x0) / (x1 - x0 || 1)) * (width - pad.l - pad.r);
  const sy = (y: number) => height - pad.b - ((y - y0) / (y1 - y0 || 1)) * (height - pad.t - pad.b);
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" role="img" aria-label={`${yLabel} against ${xLabel}`}>
      <text x={(width + pad.l) / 2} y={height - 4} textAnchor="middle" fontSize="12" fill="#a7a7a7">{xLabel}</text>
      <text x={14} y={height / 2} textAnchor="middle" fontSize="12" fill="#a7a7a7" transform={`rotate(-90 14 ${height / 2})`}>{yLabel}</text>
      {[x0, (x0 + x1) / 2, x1].map((t) => <text key={t} x={sx(t)} y={height - pad.b + 18} textAnchor="middle" fontSize="11" fill="#a7a7a7">{t.toFixed(3)}</text>)}
      {[y0, (y0 + y1) / 2, y1].map((t) => <text key={t} x={pad.l - 8} y={sy(t) + 4} textAnchor="end" fontSize="11" fill="#a7a7a7">{t.toFixed(4)}</text>)}
      <polyline fill="none" stroke="#ffffff55" strokeWidth="1.5" points={points.map((p) => `${sx(p.x)},${sy(p.y)}`).join(" ")} />
      {points.map((p, i) => <circle key={i} cx={sx(p.x)} cy={sy(p.y)} r="3" fill="#ffffff99" />)}
      {marks?.map((m) => (
        <g key={m.label}>
          <circle cx={sx(m.x)} cy={sy(m.y)} r="6" fill="none" stroke="#C8102E" strokeWidth="2" />
          <text x={sx(m.x) + 9} y={sy(m.y) - 8} fontSize="12" fill="#ffffff">{m.label}</text>
        </g>
      ))}
    </svg>
  );
}