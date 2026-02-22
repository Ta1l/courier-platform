import { FormEvent, useEffect, useState } from "react";
import axios from "axios";
import { api } from "../lib/api";
import { copyToClipboard } from "../lib/format";
import { useAuthStore } from "../store/auth";
import type { Role, User } from "../types";

type UserForm = {
  login: string;
  password: string;
  name: string;
  role: Role;
  percent: string;
};

const defaultForm: UserForm = {
  login: "",
  password: "",
  name: "",
  role: "investor",
  percent: "50",
};

function roleLabel(role: Role): string {
  return role === "admin" ? "Администратор" : "Инвестор";
}

function fieldLabel(field: string): string {
  if (field === "login") return "Логин";
  if (field === "password") return "Пароль";
  if (field === "name") return "Имя";
  if (field === "role") return "Роль";
  if (field === "percent") return "Процент";
  return field;
}

function validationMessage(item: unknown): string | null {
  if (!item || typeof item !== "object") return null;

  const error = item as {
    loc?: Array<string | number>;
    type?: string;
    msg?: string;
    ctx?: Record<string, unknown>;
  };

  const loc = Array.isArray(error.loc) ? String(error.loc[error.loc.length - 1] || "") : "";
  const field = fieldLabel(loc);

  switch (error.type) {
    case "string_too_short":
      return `${field}: минимум ${String(error.ctx?.min_length ?? "")} символов.`;
    case "string_too_long":
      return `${field}: слишком длинное значение.`;
    case "string_pattern_mismatch":
      return `${field}: допускаются только латиница, цифры, '.', '_' и '-'.`;
    case "greater_than_equal":
      return `${field}: значение должно быть не меньше ${String(error.ctx?.ge ?? 0)}.`;
    case "less_than_equal":
      return `${field}: значение должно быть не больше ${String(error.ctx?.le ?? 0)}.`;
    default:
      return error.msg ? `${field}: ${error.msg}` : null;
  }
}

function extractApiError(error: unknown, fallback: string): string {
  if (!axios.isAxiosError(error)) return fallback;

  const responseData = error.response?.data as { detail?: unknown } | undefined;
  const detail = responseData?.detail;

  if (typeof detail === "string") {
    if (detail.includes("already exists")) {
      return "Пользователь с таким логином уже существует.";
    }
    if (detail.includes("percent is required")) {
      return "Для роли инвестора укажите процент.";
    }
    if (detail.includes("Login is already taken")) {
      return "Логин уже занят.";
    }
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const msg = validationMessage(detail[0]);
    if (msg) return msg;
  }

  if (error.response?.status === 409) {
    return "Пользователь с таким логином уже существует.";
  }

  return fallback;
}

export function UsersPage() {
  const currentUser = useAuthStore((state) => state.user);

  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<UserForm>(defaultForm);
  const [submitting, setSubmitting] = useState(false);

  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<UserForm>(defaultForm);

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<User[]>("/api/users");
      setUsers(response.data);
    } catch (err: unknown) {
      setError(extractApiError(err, "Не удалось загрузить пользователей."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentUser?.role === "admin") {
      void loadUsers();
    }
  }, [currentUser?.role]);

  const onCreate = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!form.login || !form.password || !form.name) {
      setError("Заполните логин, пароль и имя.");
      return;
    }

    const login = form.login.trim();
    if (!/^[a-zA-Z0-9_.-]{3,64}$/.test(login)) {
      setError("Логин должен содержать 3-64 символа: латиница, цифры, '.', '_' или '-'.");
      return;
    }

    if (form.password.length < 8) {
      setError("Пароль должен содержать минимум 8 символов.");
      return;
    }

    const percentNumber = Number(form.percent);
    if (
      form.role === "investor" &&
      (!form.percent || Number.isNaN(percentNumber) || percentNumber < 0 || percentNumber > 100)
    ) {
      setError("Для инвестора укажите процент от 0 до 100.");
      return;
    }

    setSubmitting(true);
    try {
      await api.post<User>("/api/users", {
        login,
        password: form.password,
        name: form.name.trim(),
        role: form.role,
        percent: form.role === "investor" ? percentNumber : null,
      });
      await loadUsers();
      setForm(defaultForm);
    } catch (err: unknown) {
      setError(extractApiError(err, "Не удалось создать пользователя."));
    } finally {
      setSubmitting(false);
    }
  };

  const startEdit = (user: User) => {
    setEditingUserId(user.id);
    setEditForm({
      login: user.login,
      password: "",
      name: user.name,
      role: user.role,
      percent: String(user.percent ?? 0),
    });
  };

  const onUpdate = async (event: FormEvent) => {
    event.preventDefault();
    if (!editingUserId) return;

    try {
      await api.put<User>(`/api/users/${editingUserId}`, {
        login: editForm.login.trim(),
        password: editForm.password || undefined,
        name: editForm.name.trim(),
        role: editForm.role,
        percent: editForm.role === "investor" ? Number(editForm.percent) : null,
      });
      setEditingUserId(null);
      setEditForm(defaultForm);
      await loadUsers();
    } catch (err: unknown) {
      setError(extractApiError(err, "Не удалось обновить пользователя."));
    }
  };

  const onToggle = async (id: number) => {
    try {
      await api.patch(`/api/users/${id}/toggle`);
      await loadUsers();
    } catch (err: unknown) {
      setError(extractApiError(err, "Не удалось изменить статус пользователя."));
    }
  };

  if (currentUser?.role !== "admin") {
    return <div className="panel">Только администратор может открыть этот раздел.</div>;
  }

  return (
    <section className="stack-lg">
      <section className="panel">
        <div className="panel-header">
          <h2>Создание пользователя</h2>
        </div>
        <form className="form-grid" onSubmit={onCreate}>
          <label>
            Логин
            <input value={form.login} onChange={(event) => setForm({ ...form, login: event.target.value })} />
          </label>
          <label>
            Пароль
            <input
              type="password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
            />
          </label>
          <label>
            Имя
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
          </label>
          <label>
            Роль
            <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value as Role })}>
              <option value="investor">Инвестор</option>
              <option value="admin">Администратор</option>
            </select>
          </label>
          <label>
            Процент
            <input
              type="number"
              min={0}
              max={100}
              disabled={form.role === "admin"}
              value={form.percent}
              onChange={(event) => setForm({ ...form, percent: event.target.value })}
            />
          </label>
          <button className="button" type="submit" disabled={submitting}>
            {submitting ? "Создание..." : "Создать"}
          </button>
        </form>
        {error ? <p className="alert">{error}</p> : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Пользователи</h2>
        </div>

        {loading ? (
          <p>Загрузка пользователей...</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Логин</th>
                  <th>Имя</th>
                  <th>Роль</th>
                  <th>Процент</th>
                  <th>Активен</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>{user.id}</td>
                    <td>
                      <div className="inline-actions">
                        <span>{user.login}</span>
                        <button
                          className="button button-ghost"
                          onClick={() => copyToClipboard(user.login)}
                          type="button"
                        >
                          Копировать
                        </button>
                      </div>
                    </td>
                    <td>{user.name}</td>
                    <td>{roleLabel(user.role)}</td>
                    <td>{user.percent ?? "-"}</td>
                    <td>{user.is_active ? "Да" : "Нет"}</td>
                    <td>
                      <div className="inline-actions">
                        <button className="button button-ghost" type="button" onClick={() => startEdit(user)}>
                          Редактировать
                        </button>
                        <button className="button button-ghost" type="button" onClick={() => onToggle(user.id)}>
                          {user.is_active ? "Отключить" : "Включить"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {editingUserId ? (
        <section className="panel">
          <div className="panel-header">
            <h2>Редактирование пользователя #{editingUserId}</h2>
          </div>
          <form className="form-grid" onSubmit={onUpdate}>
            <label>
              Логин
              <input
                value={editForm.login}
                onChange={(event) => setEditForm({ ...editForm, login: event.target.value })}
              />
            </label>
            <label>
              Новый пароль (необязательно)
              <input
                type="password"
                value={editForm.password}
                onChange={(event) => setEditForm({ ...editForm, password: event.target.value })}
              />
            </label>
            <label>
              Имя
              <input
                value={editForm.name}
                onChange={(event) => setEditForm({ ...editForm, name: event.target.value })}
              />
            </label>
            <label>
              Роль
              <select
                value={editForm.role}
                onChange={(event) => setEditForm({ ...editForm, role: event.target.value as Role })}
              >
                <option value="investor">Инвестор</option>
                <option value="admin">Администратор</option>
              </select>
            </label>
            <label>
              Процент
              <input
                type="number"
                min={0}
                max={100}
                disabled={editForm.role === "admin"}
                value={editForm.percent}
                onChange={(event) => setEditForm({ ...editForm, percent: event.target.value })}
              />
            </label>
            <div className="inline-actions">
              <button className="button" type="submit">
                Сохранить
              </button>
              <button
                className="button button-ghost"
                type="button"
                onClick={() => {
                  setEditingUserId(null);
                  setEditForm(defaultForm);
                }}
              >
                Отмена
              </button>
            </div>
          </form>
        </section>
      ) : null}
    </section>
  );
}
