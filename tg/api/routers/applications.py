"""Application management routes."""

from __future__ import annotations

from datetime import date
from typing import Any

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.database import fetchall, fetchone, get_db
from api.deps import get_current_user, require_roles
from api.schemas import ApplicationOut, ApplicationUpdate

router = APIRouter(prefix="/applications", tags=["applications"])


def _serialize_application(row: dict[str, Any]) -> ApplicationOut:
    return ApplicationOut(
        id=int(row["id"]),
        telegram_id=int(row["telegram_id"]),
        username=row["username"],
        first_name=row["first_name"],
        phone=row["phone"],
        age=int(row["age"]),
        citizenship=row["citizenship"],
        source=row["source"],
        contacted=bool(row["contacted"]),
        submitted_at=row["submitted_at"],
        campaign_id=int(row["campaign_id"]) if row["campaign_id"] is not None else None,
        campaign_name=row.get("campaign_name"),
        status=row.get("status"),
        revenue=float(row["revenue"]) if row["revenue"] is not None else None,
    )


def _base_applications_query() -> str:
    return """
        SELECT
            a.id,
            a.telegram_id,
            a.username,
            a.first_name,
            a.phone,
            a.age,
            a.citizenship,
            a.source,
            a.contacted,
            a.submitted_at,
            a.campaign_id,
            a.revenue,
            COALESCE(a.status, 'new') AS status,
            c.name AS campaign_name,
            c.investor_id
        FROM applications a
        LEFT JOIN campaigns c ON c.id = a.campaign_id
        WHERE 1 = 1
    """


@router.get("", response_model=list[ApplicationOut])
async def list_applications(
    campaign: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: dict[str, Any] = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[ApplicationOut]:
    query = _base_applications_query()
    params: list[Any] = []

    if current_user["role"] == "investor":
        query += " AND c.investor_id = ?"
        params.append(int(current_user["id"]))

    if campaign is not None:
        query += " AND a.campaign_id = ?"
        params.append(int(campaign))

    if status_filter:
        query += " AND COALESCE(a.status, 'new') = ?"
        params.append(status_filter)

    if date_from:
        query += " AND a.submitted_at >= ?"
        params.append(f"{date_from.isoformat()} 00:00:00")

    if date_to:
        query += " AND a.submitted_at <= ?"
        params.append(f"{date_to.isoformat()} 23:59:59")

    query += " ORDER BY a.id DESC"

    rows = await fetchall(db, query, tuple(params))
    return [_serialize_application(row) for row in rows]


@router.put("/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
) -> ApplicationOut:
    existing = await fetchone(
        db,
        """
        SELECT
            a.id,
            a.campaign_id,
            c.investor_id
        FROM applications a
        LEFT JOIN campaigns c ON c.id = a.campaign_id
        WHERE a.id = ?
        """,
        (application_id,),
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    if (
        current_user["role"] == "investor"
        and int(existing["investor_id"] or -1) != int(current_user["id"])
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot update this application.",
        )

    changes = payload.model_dump(exclude_unset=True)
    updates: dict[str, Any] = {}
    if "status" in changes:
        updates["status"] = changes["status"]
    if "revenue" in changes:
        updates["revenue"] = changes["revenue"]

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update.",
        )

    set_clause = ", ".join(f"{field} = ?" for field in updates)
    params = list(updates.values()) + [application_id]
    await db.execute(f"UPDATE applications SET {set_clause} WHERE id = ?", params)
    await db.commit()

    row = await fetchone(
        db,
        _base_applications_query() + " AND a.id = ?",
        (application_id,),
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load updated application.",
        )

    if (
        current_user["role"] == "investor"
        and int(row["investor_id"] or -1) != int(current_user["id"])
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this application.",
        )

    return _serialize_application(row)


@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    _: dict[str, Any] = Depends(require_roles("admin")),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any]:
    exists = await fetchone(
        db,
        "SELECT id FROM applications WHERE id = ?",
        (application_id,),
    )
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    deleted_cursor = await db.execute(
        "DELETE FROM applications WHERE id = ?",
        (application_id,),
    )
    if int(deleted_cursor.rowcount or 0) == 0:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    await db.commit()
    return {
        "success": True,
        "deleted_application_id": application_id,
    }
