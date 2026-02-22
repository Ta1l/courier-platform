import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuthStore } from "../store/auth";
import type { AuthResponse } from "../types";

export function LoginPage() {
  const navigate = useNavigate();
  const accessToken = useAuthStore((state) => state.accessToken);
  const initialized = useAuthStore((state) => state.initialized);
  const initialize = useAuthStore((state) => state.initialize);
  const setSession = useAuthStore((state) => state.setSession);

  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!initialized) initialize();
  }, [initialize, initialized]);

  useEffect(() => {
    if (initialized && accessToken) {
      navigate("/dashboard", { replace: true });
    }
  }, [initialized, accessToken, navigate]);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!login.trim() || !password.trim()) {
      setError("Введите логин и пароль.");
      return;
    }

    setLoading(true);
    try {
      const response = await api.post<AuthResponse>("/api/auth/login", {
        login: login.trim(),
        password,
      });
      const data = response.data;
      setSession(data.access_token, data.refresh_token, data.user);
      navigate("/dashboard", { replace: true });
    } catch {
      setError("Неверный логин/пароль или аккаунт отключён.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-screen">
      <div className="login-card">
        <p className="eyebrow">Защищённая зона</p>
        <h1>Вход</h1>
        <p className="muted">Используйте логин и пароль для входа в админ-панель.</p>

        <form onSubmit={onSubmit} className="stack">
          <label>
            Логин
            <input
              value={login}
              onChange={(event) => setLogin(event.target.value)}
              autoComplete="username"
              placeholder="admin"
            />
          </label>

          <label>
            Пароль
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              placeholder="********"
            />
          </label>

          {error ? <div className="alert">{error}</div> : null}

          <button className="button" type="submit" disabled={loading}>
            {loading ? "Вход..." : "Войти"}
          </button>
        </form>
      </div>
    </div>
  );
}
