"""Statistics routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, status

from api.database import fetchall, fetchone, get_db
from api.deps import get_current_user
from api.metrics import calc_profit_metrics
from api.schemas import CampaignMetric, CampaignStatsResponse, DashboardResponse, DashboardTotals, TimelinePoint

router = APIRouter(prefix="/stats", tags=["stats"])


def _build_campaign_metric(row: dict[str, Any]) -> CampaignMetric:
    budget = float(row["budget"])
    percent = float(row["percent"] or 0.0)
    total_revenue = float(row["total_revenue"] or 0.0)
    computed = calc_profit_metrics(total_revenue=total_revenue, budget=budget, percent=percent)

    return CampaignMetric(
        campaign_id=int(row["id"]),
        campaign_name=row["name"],
        investor_id=int(row["investor_id"]),
        investor_name=row.get("investor_name"),
        status=row["status"],
        budget=round(budget, 2),
        percent=round(percent, 2),
        applications_count=int(row["applications_count"] or 0),
        total_revenue=computed["total_revenue"],
        net_profit=computed["net_profit"],
        investor_profit=computed["investor_profit"],
        admin_profit=computed["admin_profit"],
        roi=computed["roi"],
    )


async def _load_campaign_rows(
    db: aiosqlite.Connection,
    current_user: dict[str, Any],
) -> list[dict[str, Any]]:
    where = ""
    params: list[Any] = []
    if current_user["role"] == "investor":
        where = "WHERE c.investor_id = ?"
        params.append(int(current_user["id"]))

    query = f"""
        SELECT
            c.id,
            c.investor_id,
            c.name,
            c.budget,
            c.status,
            c.created_at,
            u.name AS investor_name,
            u.percent AS percent,
            COALESCE(SUM(a.revenue), 0) AS total_revenue,
            COUNT(a.id) AS applications_count
        FROM campaigns c
        JOIN users u ON u.id = c.investor_id
        LEFT JOIN applications a ON a.campaign_id = c.id
        {where}
        GROUP BY
            c.id, c.investor_id, c.name, c.budget, c.status, c.created_at,
            u.name, u.percent
        ORDER BY c.id DESC
    """
    return await fetchall(db, query, tuple(params))


async def _load_timeline(
    db: aiosqlite.Connection,
    current_user: dict[str, Any],
    campaign_id: int | None = None,
) -> list[TimelinePoint]:
    where_clauses = ["a.campaign_id IS NOT NULL"]
    params: list[Any] = []

    if current_user["role"] == "investor":
        where_clauses.append("c.investor_id = ?")
        params.append(int(current_user["id"]))

    if campaign_id is not None:
        where_clauses.append("a.campaign_id = ?")
        params.append(campaign_id)

    where = " AND ".join(where_clauses)
    rows = await fetchall(
        db,
        f"""
        SELECT
            substr(a.submitted_at, 1, 10) AS day,
            COALESCE(SUM(a.revenue), 0) AS revenue
        FROM applications a
        JOIN campaigns c ON c.id = a.campaign_id
        WHERE {where}
        GROUP BY day
        ORDER BY day ASC
        """,
        tuple(params),
    )
    return [
        TimelinePoint(date=row["day"], revenue=round(float(row["revenue"] or 0.0), 2))
        for row in rows
    ]


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard_stats(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
) -> DashboardResponse:
    rows = await _load_campaign_rows(db, current_user)
    campaign_metrics = [_build_campaign_metric(row) for row in rows]

    total_budget = round(sum(metric.budget for metric in campaign_metrics), 2)
    total_revenue = round(sum(metric.total_revenue for metric in campaign_metrics), 2)
    net_profit = round(sum(metric.net_profit for metric in campaign_metrics), 2)
    investor_profit = round(sum(metric.investor_profit for metric in campaign_metrics), 2)
    admin_profit = round(sum(metric.admin_profit for metric in campaign_metrics), 2)
    roi = round((net_profit / total_budget * 100.0), 2) if total_budget > 0 else 0.0

    totals = DashboardTotals(
        campaigns=len(campaign_metrics),
        total_budget=total_budget,
        total_revenue=total_revenue,
        net_profit=net_profit,
        investor_profit=investor_profit,
        admin_profit=admin_profit,
        roi=roi,
    )

    return DashboardResponse(
        totals=totals,
        campaigns=campaign_metrics,
        timeline=await _load_timeline(db, current_user),
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    )


@router.get("/campaign/{campaign_id}", response_model=CampaignStatsResponse)
async def campaign_stats(
    campaign_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
) -> CampaignStatsResponse:
    row = await fetchone(
        db,
        """
        SELECT
            c.id,
            c.investor_id,
            c.name,
            c.budget,
            c.status,
            c.created_at,
            u.name AS investor_name,
            u.percent AS percent,
            COALESCE(SUM(a.revenue), 0) AS total_revenue,
            COUNT(a.id) AS applications_count
        FROM campaigns c
        JOIN users u ON u.id = c.investor_id
        LEFT JOIN applications a ON a.campaign_id = c.id
        WHERE c.id = ?
        GROUP BY
            c.id, c.investor_id, c.name, c.budget, c.status, c.created_at,
            u.name, u.percent
        """,
        (campaign_id,),
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found.",
        )

    if (
        current_user["role"] == "investor"
        and int(row["investor_id"]) != int(current_user["id"])
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this campaign stats.",
        )

    by_status_rows = await fetchall(
        db,
        """
        SELECT COALESCE(status, 'new') AS status, COUNT(*) AS amount
        FROM applications
        WHERE campaign_id = ?
        GROUP BY COALESCE(status, 'new')
        """,
        (campaign_id,),
    )
    by_status = {row["status"]: int(row["amount"]) for row in by_status_rows}

    return CampaignStatsResponse(
        campaign=_build_campaign_metric(row),
        applications_by_status=by_status,
        timeline=await _load_timeline(db, current_user, campaign_id=campaign_id),
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    )

