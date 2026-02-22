import { FormEvent, useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { formatDate, formatMoney } from "../lib/format";
import type { Application, Campaign } from "../types";

type Filters = {
  campaign: string;
  status: string;
  date_from: string;
  date_to: string;
};

const defaultFilters: Filters = {
  campaign: "",
  status: "",
  date_from: "",
  date_to: "",
};

function applicationStatusLabel(status: string): string {
  if (status === "new") return "Новая";
  if (status === "in_progress") return "В работе";
  if (status === "approved") return "Одобрена";
  if (status === "rejected") return "Отклонена";
  return status;
}

export function ApplicationsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [drafts, setDrafts] = useState<Record<number, { status: string; revenue: string }>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCampaigns = async () => {
    try {
      const response = await api.get<Campaign[]>("/api/campaigns");
      setCampaigns(response.data);
    } catch {
      setError("Не удалось загрузить кампании для фильтров.");
    }
  };

  const fetchApplications = async () => {
    setLoading(true);
    setError(null);

    const params: Record<string, string> = {};
    if (filters.campaign) params.campaign = filters.campaign;
    if (filters.status) params.status = filters.status;
    if (filters.date_from) params.date_from = filters.date_from;
    if (filters.date_to) params.date_to = filters.date_to;

    try {
      const response = await api.get<Application[]>("/api/applications", { params });
      setApplications(response.data);
      const nextDrafts: Record<number, { status: string; revenue: string }> = {};
      for (const application of response.data) {
        nextDrafts[application.id] = {
          status: application.status || "new",
          revenue: application.revenue == null ? "" : String(application.revenue),
        };
      }
      setDrafts(nextDrafts);
    } catch {
      setError("Не удалось загрузить заявки.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchCampaigns();
  }, []);

  useEffect(() => {
    void fetchApplications();
  }, []);

  const totalRevenue = useMemo(
    () => applications.reduce((sum, item) => sum + (item.revenue || 0), 0),
    [applications],
  );

  const onApplyFilters = (event: FormEvent) => {
    event.preventDefault();
    void fetchApplications();
  };

  const onSaveRow = async (applicationId: number) => {
    const draft = drafts[applicationId];
    if (!draft) return;

    try {
      await api.put(`/api/applications/${applicationId}`, {
        status: draft.status,
        revenue: draft.revenue.trim() === "" ? null : Number(draft.revenue),
      });
      await fetchApplications();
    } catch {
      setError("Не удалось обновить заявку.");
    }
  };

  return (
    <section className="stack-lg">
      <section className="panel">
        <div className="panel-header">
          <h2>Фильтры</h2>
          <strong>{formatMoney(totalRevenue)}</strong>
        </div>
        <form className="form-grid" onSubmit={onApplyFilters}>
          <label>
            Кампания
            <select
              value={filters.campaign}
              onChange={(event) => setFilters({ ...filters, campaign: event.target.value })}
            >
              <option value="">Все кампании</option>
              {campaigns.map((campaign) => (
                <option key={campaign.id} value={String(campaign.id)}>
                  {campaign.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Статус
            <select value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">Любой</option>
              <option value="new">Новая</option>
              <option value="in_progress">В работе</option>
              <option value="approved">Одобрена</option>
              <option value="rejected">Отклонена</option>
            </select>
          </label>
          <label>
            Дата с
            <input
              type="date"
              value={filters.date_from}
              onChange={(event) => setFilters({ ...filters, date_from: event.target.value })}
            />
          </label>
          <label>
            Дата по
            <input
              type="date"
              value={filters.date_to}
              onChange={(event) => setFilters({ ...filters, date_to: event.target.value })}
            />
          </label>
          <div className="inline-actions">
            <button className="button" type="submit">
              Применить
            </button>
            <button
              className="button button-ghost"
              type="button"
              onClick={() => {
                setFilters(defaultFilters);
                void fetchApplications();
              }}
            >
              Сбросить
            </button>
          </div>
        </form>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Заявки</h2>
        </div>

        {loading ? <p>Загрузка заявок...</p> : null}
        {error ? <p className="alert">{error}</p> : null}

        {!loading ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Кампания</th>
                  <th>Имя</th>
                  <th>Телефон</th>
                  <th>Статус</th>
                  <th>Выручка</th>
                  <th>Дата</th>
                  <th>Действие</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((application) => {
                  const draft = drafts[application.id] || {
                    status: application.status || "new",
                    revenue: application.revenue == null ? "" : String(application.revenue),
                  };
                  return (
                    <tr key={application.id}>
                      <td>{application.id}</td>
                      <td>{application.campaign_name || application.campaign_id || "-"}</td>
                      <td>{application.first_name || application.username || "-"}</td>
                      <td>{application.phone}</td>
                      <td>
                        <select
                          value={draft.status}
                          onChange={(event) =>
                            setDrafts({
                              ...drafts,
                              [application.id]: { ...draft, status: event.target.value },
                            })
                          }
                        >
                          <option value="new">{applicationStatusLabel("new")}</option>
                          <option value="in_progress">{applicationStatusLabel("in_progress")}</option>
                          <option value="approved">{applicationStatusLabel("approved")}</option>
                          <option value="rejected">{applicationStatusLabel("rejected")}</option>
                        </select>
                      </td>
                      <td>
                        <input
                          type="number"
                          min={0}
                          step={0.01}
                          value={draft.revenue}
                          onChange={(event) =>
                            setDrafts({
                              ...drafts,
                              [application.id]: { ...draft, revenue: event.target.value },
                            })
                          }
                        />
                      </td>
                      <td>{formatDate(application.submitted_at)}</td>
                      <td>
                        <button className="button button-ghost" type="button" onClick={() => onSaveRow(application.id)}>
                          Сохранить
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </section>
  );
}
