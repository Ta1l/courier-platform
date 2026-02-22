import { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { formatMoney, formatPercent } from "../lib/format";
import type { DashboardResponse } from "../types";

function statusLabel(status: string): string {
  if (status === "active") return "Активна";
  if (status === "paused") return "Пауза";
  return status;
}

export function DashboardPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .get<DashboardResponse>("/api/stats/dashboard")
      .then((response) => setData(response.data))
      .catch(() => setError("Не удалось загрузить статистику дашборда."))
      .finally(() => setLoading(false));
  }, []);

  const maxRevenue = useMemo(() => {
    if (!data?.timeline.length) return 1;
    return Math.max(...data.timeline.map((point) => point.revenue), 1);
  }, [data]);

  if (loading) {
    return <div className="panel">Загрузка дашборда...</div>;
  }

  if (error || !data) {
    return <div className="panel alert">{error || "Нет данных"}</div>;
  }

  return (
    <section className="stack-lg">
      <div className="card-grid">
        <article className="metric-card">
          <h3>Оборот</h3>
          <strong>{formatMoney(data.totals.total_revenue)}</strong>
        </article>
        <article className="metric-card">
          <h3>Чистая прибыль</h3>
          <strong>{formatMoney(data.totals.net_profit)}</strong>
        </article>
        <article className="metric-card">
          <h3>ROI</h3>
          <strong>{formatPercent(data.totals.roi)}</strong>
        </article>
        <article className="metric-card">
          <h3>Кампании</h3>
          <strong>{data.totals.campaigns}</strong>
        </article>
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Динамика выручки</h2>
          <small>{data.generated_at}</small>
        </div>
        {data.timeline.length === 0 ? (
          <p className="muted">Пока нет данных о выручке.</p>
        ) : (
          <div className="chart-bars">
            {data.timeline.map((point) => {
              const height = Math.max(8, Math.round((point.revenue / maxRevenue) * 100));
              return (
                <div key={point.date} className="chart-column" title={`${point.date}: ${formatMoney(point.revenue)}`}>
                  <div className="chart-bar" style={{ height: `${height}%` }} />
                  <span>{point.date.slice(5)}</span>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Эффективность кампаний</h2>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Кампания</th>
                <th>Статус</th>
                <th>Бюджет</th>
                <th>Оборот</th>
                <th>Чистая прибыль</th>
                <th>ROI</th>
              </tr>
            </thead>
            <tbody>
              {data.campaigns.map((campaign) => (
                <tr key={campaign.campaign_id}>
                  <td>{campaign.campaign_name}</td>
                  <td>{statusLabel(campaign.status)}</td>
                  <td>{formatMoney(campaign.budget)}</td>
                  <td>{formatMoney(campaign.total_revenue)}</td>
                  <td>{formatMoney(campaign.net_profit)}</td>
                  <td>{formatPercent(campaign.roi)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}
