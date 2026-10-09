import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useCollections, useHome, useMe, useSetMode } from "../api/hooks";
import type { Mode } from "../api/types";
import DiscoveryModeControl from "../components/discovery/DiscoveryModeControl";
import TonightPanel from "../components/discovery/TonightPanel";
import Hero from "../components/hero/Hero";
import { PageMessage, RailSkeleton } from "../components/Loading";
import Rail from "../components/rail/Rail";

const PERSONAL = new Set(["top_picks", "based_on_ratings", "people_like_you", "different"]);

export default function Home() {
  const me = useMe();
  const [mode, setMode] = useState<Mode | undefined>(undefined);
  const home = useHome(mode);
  const saveMode = useSetMode();
  const [tonight, setTonight] = useState(false);
  const collections = useCollections();

  if (me.data && !me.data.onboarded) return <Navigate to="/onboarding" replace />;
  if (home.isError) return <PageMessage title="Recommendations are not ready">{(home.error as Error).message}</PageMessage>;
  const active: Mode = mode ?? home.data?.mode ?? me.data?.discovery_mode ?? "balanced";
  return (
    <div>
      {home.data ? <Hero items={home.data.hero} /> : <div className="h-[78vh] animate-pulse bg-surface" />}
      <div className="relative z-10 -mt-8 space-y-2">
        <div className="flex flex-wrap items-center gap-4 px-4 pb-4 md:px-10">
          <DiscoveryModeControl
            value={active}
            onChange={(m) => {
              setMode(m);
              saveMode.mutate(m);
            }}
          />
          <button onClick={() => setTonight((t) => !t)} aria-expanded={tonight}
            className="rounded-full border border-white/20 px-4 py-2 text-sm hover:border-white/50">
            For Tonight
          </button>
          <Link to="/discover" className="text-sm text-muted hover:text-white">Browse everything →</Link>
        </div>
        {tonight && (
          <div className="px-4 pb-6 md:px-10">
            <TonightPanel />
          </div>
        )}
        {home.isLoading && [0, 1, 2].map((i) => <RailSkeleton key={i} />)}
        <div className="space-y-6">
          {home.data?.rails.map((r) => (
            <Rail key={r.key} title={r.title} items={r.items} source={`rail:${r.key.split(":")[0]}`}
              personal={PERSONAL.has(r.key) || r.items.some((i) => i.match_pct != null)} />
          ))}
          {home.data && collections.data?.collections.map((c) => (
            <Rail key={c.key} title={c.title} subtitle={`${c.count.toLocaleString()} films`} items={c.items}
              source={`collection:${c.key}`} personal={c.items.some((i) => i.match_pct != null)} />
          ))}
        </div>
      </div>
    </div>
  );
}