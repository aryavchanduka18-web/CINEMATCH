import { NavLink } from "react-router-dom";
import { TABS } from "./NavBar";

/** Phones (< 768px): a floating pill tab bar at the bottom, within thumb reach; desktop keeps the top bar. */
export default function MobileTabBar() {
  return (
    <nav aria-label="Main" className="fixed inset-x-3 bottom-3 z-40 md:hidden" style={{ paddingBottom: "env(safe-area-inset-bottom)" }}>
      <div className="mx-auto grid max-w-md grid-cols-5 rounded-full border border-white/10 bg-black/80 p-1 shadow-2xl backdrop-blur-md">
        {TABS.map((t) => (
          <NavLink
            key={t.to}
            to={t.to}
            end={t.to === "/"}
            className={({ isActive }) =>
              `rounded-full py-2.5 text-center text-[11px] transition-colors ${isActive ? "bg-white font-semibold text-black" : "text-white/70"}`
            }
          >
            {t.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
