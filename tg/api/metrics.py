"""Metrics calculations for dashboard and campaign stats."""

from __future__ import annotations


def _as_float(value: object) -> float:
    if value is None:
        return 0.0
    return float(value)


def calc_profit_metrics(total_revenue: float, budget: float, percent: float) -> dict[str, float]:
    total_revenue = _as_float(total_revenue)
    budget = _as_float(budget)
    percent = _as_float(percent)

    net_profit = total_revenue - budget
    investor_profit = net_profit * percent / 100.0
    admin_profit = net_profit - investor_profit
    roi = (net_profit / budget * 100.0) if budget > 0 else 0.0

    return {
        "total_revenue": round(total_revenue, 2),
        "net_profit": round(net_profit, 2),
        "investor_profit": round(investor_profit, 2),
        "admin_profit": round(admin_profit, 2),
        "roi": round(roi, 2),
    }

