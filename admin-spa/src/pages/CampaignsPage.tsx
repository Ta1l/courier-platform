import { FormEvent, useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { copyToClipboard, formatMoney } from "../lib/format";
import { useAuthStore } from "../store/auth";
import type { Campaign, User } from "../types";

type CampaignForm = {
  investor_id: string;
  name: string;
  budget: string;
  status: "active" | "paused";
};

const defaultForm: CampaignForm = {
  investor_id: "",
  name: "",
  budget: "0",
  status: "active",
};

function statusLabel(status: "active" | "paused"): string {
  return status === "active" ? "Активна" : "Пауза";
}

export function CampaignsPage() {
  const currentUser = useAuthStore((state) => state.user);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [investors, setInvestors] = useState<User[]>([]);
  const [form, setForm] = useState<CampaignForm>(defaultForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<CampaignForm>(defaultForm);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const siteBaseUrl = useMemo(() => {
    const fromEnv = String(import.meta.env.VITE_SITE_BASE_URL || "").trim();
    return fromEnv || window.location.origin;
  }, []);

  const loadCampaigns = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<Campaign[]>("/api/campaigns");
      setCampaigns(response.data);
    } catch {
      setError("Не удалось загрузить кампании.");
    } finally {
      setLoading(false);
    }
  };

  const loadInvestors = async () => {
    if (currentUser?.role !== "admin") return;
    try {
      const response = await api.get<User[]>("/api/users");
      const onlyInvestors = response.data.filter((user) => user.role === "investor" && user.is_active);
      setInvestors(onlyInvestors);
      if (!form.investor_id && onlyInvestors[0]) {
        setForm((state) => ({ ...state, investor_id: String(onlyInvestors[0].id) }));
      }
    } catch {
      setError("Не удалось загрузить список инвесторов.");
    }
  };

  useEffect(() => {
    void loadCampaigns();
    void loadInvestors();
  }, [currentUser?.role]);

  const onCreate = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!form.name.trim()) {
      setError("Введите название кампании.");
      return;
    }

    const budget = Number(form.budget);
    if (Number.isNaN(budget) || budget < 0) {
      setError("Бюджет должен быть неотрицательным числом.");
      return;
    }

    try {
      await api.post("/api/campaigns", {
        name: form.name.trim(),
        budget,
        status: form.status,
        investor_id: currentUser?.role === "admin" ? Number(form.investor_id) : undefined,
      });
      setForm(defaultForm);
      await loadCampaigns();
    } catch {
      setError("Не удалось создать кампанию.");
    }
  };

  const startEdit = (campaign: Campaign) => {
    setEditingId(campaign.id);
    setEditForm({
      investor_id: String(campaign.investor_id),
      name: campaign.name,
      budget: String(campaign.budget),
      status: campaign.status,
    });
  };

  const onUpdate = async (event: FormEvent) => {
    event.preventDefault();
    if (!editingId) return;

    try {
      await api.put(`/api/campaigns/${editingId}`, {
        name: editForm.name.trim(),
        budget: Number(editForm.budget),
        status: editForm.status,
        investor_id: currentUser?.role === "admin" ? Number(editForm.investor_id) : undefined,
      });
      setEditingId(null);
      setEditForm(defaultForm);
      await loadCampaigns();
    } catch {
      setError("Не удалось обновить кампанию.");
    }
  };

  const toggleStatus = async (campaign: Campaign) => {
    const nextStatus = campaign.status === "active" ? "paused" : "active";
    try {
      await api.patch(`/api/campaigns/${campaign.id}/status`, { status: nextStatus });
      await loadCampaigns();
    } catch {
      setError("Не удалось изменить статус кампании.");
    }
  };

  const deleteCampaign = async (campaign: Campaign) => {
    if (currentUser?.role !== "admin") return;
    const approved = window.confirm(
      `Удалить кампанию "${campaign.name}" (ID ${campaign.id}) и все связанные заявки?`,
    );
    if (!approved) return;

    try {
      await api.delete(`/api/campaigns/${campaign.id}`);
      if (editingId === campaign.id) {
        setEditingId(null);
      }
      await loadCampaigns();
    } catch {
      setError("Не удалось удалить кампанию.");
    }
  };

  return (
    <section className="stack-lg">
      <section className="panel">
        <div className="panel-header">
          <h2>Создание кампании</h2>
        </div>
        <form className="form-grid" onSubmit={onCreate}>
          {currentUser?.role === "admin" ? (
            <label>
              Инвестор
              <select
                value={form.investor_id}
                onChange={(event) => setForm({ ...form, investor_id: event.target.value })}
                required
              >
                {investors.map((investor) => (
                  <option key={investor.id} value={String(investor.id)}>
                    {investor.name} ({investor.login})
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          <label>
            Название
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          </label>
          <label>
            Бюджет
            <input
              type="number"
              min={0}
              step={0.01}
              value={form.budget}
              onChange={(event) => setForm({ ...form, budget: event.target.value })}
              required
            />
          </label>
          <button className="button" type="submit">
            Создать
          </button>
        </form>
        {error ? <p className="alert">{error}</p> : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Кампании</h2>
        </div>
        {loading ? (
          <p>Загрузка кампаний...</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Название</th>
                  <th>Инвестор</th>
                  <th>Бюджет</th>
                  <th>Статус</th>
                  <th>Ссылка</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {campaigns.map((campaign) => {
                  const trackingLink = `${siteBaseUrl}/?camp=${campaign.id}`;
                  return (
                    <tr key={campaign.id}>
                      <td>{campaign.id}</td>
                      <td>{campaign.name}</td>
                      <td>{campaign.investor_name || campaign.investor_login || campaign.investor_id}</td>
                      <td>{formatMoney(campaign.budget)}</td>
                      <td>{statusLabel(campaign.status)}</td>
                      <td>
                        <button
                          className="button button-ghost"
                          type="button"
                          onClick={() => copyToClipboard(trackingLink)}
                        >
                          Копировать ссылку
                        </button>
                      </td>
                      <td>
                        <div className="inline-actions">
                          <button className="button button-ghost" type="button" onClick={() => startEdit(campaign)}>
                            Редактировать
                          </button>
                          <button className="button button-ghost" type="button" onClick={() => toggleStatus(campaign)}>
                            {campaign.status === "active" ? "Поставить на паузу" : "Активировать"}
                          </button>
                          {currentUser?.role === "admin" ? (
                            <button className="button button-ghost" type="button" onClick={() => deleteCampaign(campaign)}>
                              Удалить
                            </button>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {editingId ? (
        <section className="panel">
          <div className="panel-header">
            <h2>Редактирование кампании #{editingId}</h2>
          </div>
          <form className="form-grid" onSubmit={onUpdate}>
            {currentUser?.role === "admin" ? (
              <label>
                Инвестор
                <select
                  value={editForm.investor_id}
                  onChange={(event) => setEditForm({ ...editForm, investor_id: event.target.value })}
                >
                  {investors.map((investor) => (
                    <option key={investor.id} value={String(investor.id)}>
                      {investor.name} ({investor.login})
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <label>
              Название
              <input
                value={editForm.name}
                onChange={(event) => setEditForm({ ...editForm, name: event.target.value })}
                required
              />
            </label>
            <label>
              Бюджет
              <input
                type="number"
                min={0}
                step={0.01}
                value={editForm.budget}
                onChange={(event) => setEditForm({ ...editForm, budget: event.target.value })}
                required
              />
            </label>
            <label>
              Статус
              <select
                value={editForm.status}
                onChange={(event) =>
                  setEditForm({ ...editForm, status: event.target.value as "active" | "paused" })
                }
              >
                <option value="active">Активна</option>
                <option value="paused">Пауза</option>
              </select>
            </label>
            <div className="inline-actions">
              <button className="button" type="submit">
                Сохранить
              </button>
              <button className="button button-ghost" type="button" onClick={() => setEditingId(null)}>
                Отмена
              </button>
            </div>
          </form>
        </section>
      ) : null}
    </section>
  );
}
