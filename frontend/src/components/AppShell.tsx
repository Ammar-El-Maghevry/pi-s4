import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";

export function AppShell() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { language, toggleLanguage, t } = useLanguage();

  const ADMIN_NAV = [
    { to: "/", label: t.nav.dashboard, end: true },
    { to: "/people", label: t.nav.people },
    { to: "/schedules", label: t.nav.schedules },
    { to: "/cameras", label: t.nav.cameras },
    { to: "/attendance", label: t.nav.attendance },
    { to: "/reports", label: t.nav.reports },
  ];
  const SELF_NAV = [{ to: "/reports", label: t.nav.myReport, end: true }];
  const nav = user?.role === "admin" ? ADMIN_NAV : SELF_NAV;

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-56 shrink-0 flex-col border-r border-border bg-bg-elevated">
        <div className="flex items-center gap-2 border-b border-border px-5 py-4">
          <span className="h-2.5 w-2.5 shrink-0 animate-pulse rounded-full bg-accent" />
          <span className="font-heading text-base font-semibold tracking-tight">
            Presence.sys
          </span>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-3">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-accent-soft text-accent"
                    : "text-text-muted hover:bg-bg-inset hover:text-text"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border bg-bg-elevated px-6 py-3">
          <div className="font-data text-xs text-text-muted">
            {new Date().toLocaleDateString(language === "fr" ? "fr-FR" : undefined, {
              weekday: "long",
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={toggleLanguage}
              className="rounded-md border border-border px-3 py-1.5 text-sm text-text-muted hover:text-text"
              aria-label={t.shell.toggleLanguage}
            >
              {language === "fr" ? "FR" : "EN"}
            </button>
            <button
              onClick={toggleTheme}
              className="rounded-md border border-border px-3 py-1.5 text-sm text-text-muted hover:text-text"
              aria-label={t.shell.toggleTheme}
            >
              {theme === "dark" ? t.shell.light : t.shell.dark}
            </button>
            <div className="flex items-center gap-2 text-sm">
              <span className="font-medium">{user?.full_name}</span>
              <span className="rounded-full bg-bg-inset px-2 py-0.5 text-xs font-data uppercase text-text-muted">
                {user?.role}
              </span>
            </div>
            <button
              onClick={logout}
              className="rounded-md border border-border px-3 py-1.5 text-sm text-text-muted hover:border-absent/50 hover:text-absent"
            >
              {t.shell.logout}
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
