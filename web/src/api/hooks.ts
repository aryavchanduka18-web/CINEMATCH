import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, send } from "./client";
import type { HomePayload, Me, Mode, MovieDetail, RecItem } from "./types";

export const useMe = () => useQuery({ queryKey: ["me"], queryFn: () => api<Me>("/me"), staleTime: 30_000 });

export const useHome = (mode?: Mode) =>
  useQuery({ queryKey: ["home", mode ?? "saved"], queryFn: () => api<HomePayload>(`/recs/home${mode ? `?mode=${mode}` : ""}`) });

export const useMovie = (id: number) => useQuery({ queryKey: ["movie", id], queryFn: () => api<MovieDetail>(`/movies/${id}`) });

export const useSimilar = (id: number) =>
  useQuery({ queryKey: ["similar", id], queryFn: () => api<{ items: RecItem[] }>(`/movies/${id}/similar`) });

type FeedbackAction =
  | { kind: "rate"; rating: number | null }
  | { kind: "react"; value: 1 | -1 | 0 }
  | { kind: "list"; on: boolean }
  | { kind: "watched"; on: boolean };

/** Like / dislike / list / watched / rate with an immediate refresh of everything personal (spec 6.12). */
export function useFeedback(movieId: number, source?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (a: FeedbackAction) => {
      switch (a.kind) {
        case "rate":
          return a.rating ? send("PUT", `/ratings/${movieId}`, { rating: a.rating, source }) : send("DELETE", `/ratings/${movieId}`);
        case "react":
          return a.value ? send("PUT", `/reactions/${movieId}`, { value: a.value, source }) : send("DELETE", `/reactions/${movieId}`);
        case "list":
          return a.on ? send("PUT", `/list/${movieId}`, { source }) : send("DELETE", `/list/${movieId}`);
        case "watched":
          return a.on ? send("PUT", `/watched/${movieId}`) : send("DELETE", `/watched/${movieId}`);
      }
    },
    onSettled: () => {
      for (const key of ["home", "movie", "me", "list", "activity", "genre", "taste"]) qc.invalidateQueries({ queryKey: [key] });
    },
  });
}

export function useLogEvent() {
  return (event_type: "detail_view" | "quick_view" | "search_click" | "hero_view", movie_id: number, source?: string, position?: number) =>
    send("POST", "/events", { event_type, movie_id, source, position }).catch(() => undefined);
}

export function useSetMode() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (mode: Mode) => send("PUT", "/me/preferences", { discovery_mode: mode }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["me"] });
      qc.invalidateQueries({ queryKey: ["home"] });
    },
  });
}