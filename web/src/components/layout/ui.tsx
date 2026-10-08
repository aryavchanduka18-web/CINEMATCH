import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import type { RecItem } from "../../api/types";

type UI = {
  quickView: RecItem | null;
  openQuickView: (item: RecItem) => void;
  closeQuickView: () => void;
  toast: string | null;
  notify: (msg: string) => void;
};

const Ctx = createContext<UI | null>(null);

export function UIProvider({ children }: { children: ReactNode }) {
  const [quickView, setQuickView] = useState<RecItem | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const notify = useCallback((msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast((t) => (t === msg ? null : t)), 2200);
  }, []);
  return (
    <Ctx.Provider value={{ quickView, openQuickView: setQuickView, closeQuickView: () => setQuickView(null), toast, notify }}>
      {children}
    </Ctx.Provider>
  );
}

export function useUI(): UI {
  const v = useContext(Ctx);
  if (!v) throw new Error("useUI outside UIProvider");
  return v;
}