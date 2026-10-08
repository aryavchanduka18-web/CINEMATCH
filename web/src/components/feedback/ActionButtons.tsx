import { useFeedback } from "../../api/hooks";
import type { UserState } from "../../api/types";
import { useUI } from "../layout/ui";

type Props = { movieId: number; state: UserState; source?: string; size?: "sm" | "md"; showWatched?: boolean };

const Icon = {
  like: (on: boolean) => (
    <svg viewBox="0 0 24 24" className="h-[1.1em] w-[1.1em]" fill={on ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.8">
      <path d="M7 11v9H4v-9h3Zm0 0 4-7a2 2 0 0 1 2 2v4h5.5a2 2 0 0 1 2 2.3l-1.2 6A2 2 0 0 1 17.3 20H7" />
    </svg>
  ),
  dislike: (on: boolean) => (
    <svg viewBox="0 0 24 24" className="h-[1.1em] w-[1.1em] rotate-180" fill={on ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.8">
      <path d="M7 11v9H4v-9h3Zm0 0 4-7a2 2 0 0 1 2 2v4h5.5a2 2 0 0 1 2 2.3l-1.2 6A2 2 0 0 1 17.3 20H7" />
    </svg>
  ),
  list: (on: boolean) => (
    <svg viewBox="0 0 24 24" className="h-[1.1em] w-[1.1em]" fill="none" stroke="currentColor" strokeWidth="1.9">
      {on ? <path d="m5 12 4.5 4.5L19 7" /> : <path d="M12 5v14M5 12h14" />}
    </svg>
  ),
  watched: (on: boolean) => (
    <svg viewBox="0 0 24 24" className="h-[1.1em] w-[1.1em]" fill={on ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.8">
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
      <circle cx="12" cy="12" r="3" fill={on ? "#080808" : "none"} />
    </svg>
  ),
};

export default function ActionButtons({ movieId, state, source, size = "sm", showWatched = false }: Props) {
  const fb = useFeedback(movieId, source);
  const { notify } = useUI();
  const cls = `grid place-items-center rounded-full border transition-colors duration-150 ${
    size === "sm" ? "h-8 w-8 text-sm" : "h-11 w-11 text-base"
  }`;
  const off = "border-white/30 bg-black/40 text-white hover:border-white";
  const on = "border-white bg-white text-black";
  return (
    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
      <button
        className={`${cls} ${state.in_list ? on : off}`}
        aria-pressed={state.in_list}
        aria-label={state.in_list ? "Remove from My List" : "Add to My List"}
        title={state.in_list ? "Remove from My List" : "Add to My List"}
        onClick={() => {
          fb.mutate({ kind: "list", on: !state.in_list });
          notify(state.in_list ? "Removed from My List" : "Added to My List");
        }}
      >
        {Icon.list(state.in_list)}
      </button>
      <button
        className={`${cls} ${state.reaction === 1 ? on : off}`}
        aria-pressed={state.reaction === 1}
        aria-label="Like"
        title="Like"
        onClick={() => fb.mutate({ kind: "react", value: state.reaction === 1 ? 0 : 1 })}
      >
        {Icon.like(state.reaction === 1)}
      </button>
      <button
        className={`${cls} ${state.reaction === -1 ? on : off}`}
        aria-pressed={state.reaction === -1}
        aria-label="Dislike"
        title="Not for me"
        onClick={() => {
          fb.mutate({ kind: "react", value: state.reaction === -1 ? 0 : -1 });
          if (state.reaction !== -1) notify("Got it. We won't show this again.");
        }}
      >
        {Icon.dislike(state.reaction === -1)}
      </button>
      {showWatched && (
        <button
          className={`${cls} ${state.watched ? on : off}`}
          aria-pressed={state.watched}
          aria-label={state.watched ? "Unmark watched" : "Mark watched"}
          title={state.watched ? "Watched" : "Mark watched"}
          onClick={() => fb.mutate({ kind: "watched", on: !state.watched })}
        >
          {Icon.watched(state.watched)}
        </button>
      )}
    </div>
  );
}