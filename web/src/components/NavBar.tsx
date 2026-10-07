import { NavLink } from "react-router-dom";

export const TABS = [
  { to: "/", label: "Home" },
  { to: "/discover", label: "Discover" },
  { to: "/genres", label: "Genres" },
  { to: "/my-list", label: "My List" },
  { to: "/activity", label: "Activity" },
];

export default function NavBar() {
  return (
    <header className="flex items-center gap-8 border-b border-white/10 px-6 py-4">
      <span className="text-lg font-semibold">CineMatch</span>
      <nav className="flex gap-5 text-sm">
        {TABS.map((t) => (
          <NavLink
            key={t.to}
            to={t.to}
            end={t.to === "/"}
            className={({ isActive }) => (isActive ? "text-white" : "text-white/60 hover:text-white")}
          >
            {t.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}