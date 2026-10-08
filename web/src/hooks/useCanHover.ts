import { useEffect, useState } from "react";

/** True on devices with a real pointer. Touch devices never get hover-only UI (spec 8.4). */
export function useCanHover(): boolean {
  const query = "(hover: hover) and (pointer: fine)";
  const [can, setCan] = useState(() => typeof window !== "undefined" && window.matchMedia?.(query).matches);
  useEffect(() => {
    const mq = window.matchMedia?.(query);
    if (!mq) return;
    const on = () => setCan(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return !!can;
}