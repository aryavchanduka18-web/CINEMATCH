import { NavLink } from "react-router-dom";
import { TABS } from "./NavBar";

/** Bottom tab bar on phones (< 768px), spec 8.1. */
export default function MobileTabBar() {
  return (
    <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 border-t border-white/10 bg-bg/95 md:hidden">
      {TABS.map((t) => (
        <NavLink
          key={t.to}
          to={t.to}
          end={t.to === "/"}
          className={({ isActive }) => `py-3 text-center text-[11px] ${isActive ? "font-semibold text-white" : "text-muted"}`}
        >
          {t.label}
        </NavLink>
      ))}
    </nav>
  );
}