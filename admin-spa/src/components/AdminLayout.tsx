import { useEffect, useMemo } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuthStore } from "../store/auth";
import type { User } from "../types";

function linkClass({ isActive }: { isActive: boolean }) {
  return isActive ? "nav-link nav-link-active" : "nav-link";
}

function roleLabel(role?: string): string {
  if (role === "admin") return "Администратор";
  if (role === "investor") return "Инвестор";
  return "Гость";
}

export function AdminLayout() {
  const navigate = useNavigate();
  const accessToken = useAuthStore((state) => state.accessToken);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const clearSession = useAuthStore((state) => state.clearSession);

  useEffect(() => {
    if (!accessToken || user) return;

    api
      .get<User>("/api/auth/me")
      .then((response) => setUser(response.data))
      .catch(() => {
        clearSession();
        navigate("/login", { replace: true });
      });
  }, [accessToken, user, setUser, clearSession, navigate]);

  const navItems = useMemo(() => {
    const base = [
      { to: "/dashboard", label: "Дашборд" },
      { to: "/campaigns", label: "Кампании" },
      { to: "/applications", label: "Заявки" },
    ];
    if (user?.role === "admin") {
      base.splice(1, 0, { to: "/users", label: "Пользователи" });
    }
    return base;
  }, [user?.role]);

  const logout = async () => {
    try {
      if (refreshToken) {
        await api.post("/api/auth/logout", { refresh_token: refreshToken });
      } else {
        await api.post("/api/auth/logout", {});
      }
    } catch {
      // Ignore network issues during logout.
    } finally {
      clearSession();
      navigate("/login", { replace: true });
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Управление</p>
          <h1>Панель управления рекламой</h1>
        </div>
        <div className="topbar-actions">
          <div className="user-chip">
            <span>{user?.name || "Неизвестный пользователь"}</span>
            <small>{roleLabel(user?.role)}</small>
          </div>
          <button className="button button-ghost" onClick={logout}>
            Выйти
          </button>
        </div>
      </header>

      <div className="layout-grid">
        <aside className="sidebar">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} className={linkClass}>
              {item.label}
            </NavLink>
          ))}
        </aside>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
