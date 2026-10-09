import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import type { RecItem } from "../../api/types";

type UI = {
  quickView: RecItem | null;
  openQuickView: (item: RecItem) => void;
  closeQuickView: () => void;
  toast: string | null;
  notify: (msg: string) => void;
  /** Film whose "Why?" panel is open. */
  whyId: number | null;
  openWhy: (movieId: number | null) => void;
  /** Film just disliked: the "why not?" sheet asks for a reason. */
  dislikeId: number | null;
  askDislikeReason: (movieId: number | null) => void;
};

const Ctx = createContext<UI | null>(null);

export function UIProvider({ children }: { children: ReactNode }) {
  const [quickView, setQuickView] = useState<RecItem | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [whyId, setWhyId] = useState<number | null>(null);
  const [dislikeId, setDislikeId] = useState<number | null>(null);
  const notify = useCallback((msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast((t) => (t === msg ? null : t)), 2600);
  }, []);
  return (
    <Ctx.Provider value={{ quickView, openQuickView: setQuickView, closeQuickView: () => setQuickView(null), toast, notify,
      whyId, openWhy: setWhyId, dislikeId, askDislikeReason: setDislikeId }}>
      {children}
    </Ctx.Provider>
  );
}

export function useUI(): UI {
  const v = useContext(Ctx);
  if (!v) throw new Error("useUI outside UIProvider");
  return v;
}
