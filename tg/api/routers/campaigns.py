"""Campaign management routes."""

from __future__ import annotations

from typing import Any

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, status

from api.database import fetchall, fetchone, get_db
from api.deps import get_current_user, require_roles
from api.schemas import CampaignCreate, CampaignOut, CampaignStatusUpdate, CampaignUpdate

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _serialize_campaign(campaign: dict[str, Any]) -> CampaignOut:
    return CampaignOut(
        id=int(campaign["id"]),
        investor_id=int(campaign["investor_id"]),
        investor_login=campaign.get("investor_login"),
        investor_name=campaign.get("investor_name"),
        name=campaign["name"],
        budget=float(campaign["budget"]),
        status=campaign["status"],
        created_at=campaign["created_at"],
    )


async def _fetch_campaign(db: aiosqlite.Connection, campaign_id: int) -> dict[str, Any] | None:
    return await fetchone(
        db,
        """
        SELECT
            c.id,
            c.investor_id,
            c.name,
            c.budget,
            c.status,
            c.created_at,
            u.login AS investor_login,
            u.name AS investor_name
        FROM campaigns c
        JOIN users u ON u.id = c.investor_id
        WHERE c.id = ?
        """,
        (campaign_id,),
    )


async def _validate_investor(db: aiosqlite.Connection, investor_id: int) -> None:
    investor = await fetchone(
        db,
        "SELECT id, role, is_active FROM users WHERE id = ?",
        (investor_id,),
    )
    if not investor or investor["role"] != "investor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="investor_id must reference an investor user.",
        )
    if not investor["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Investor account is inactive.",
        )


@router.get("", response_model=list[CampaignOut])
async def list_campaigns(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[CampaignOut]:
    if current_user["role"] == "admin":
        campaigns = await fetchall(
            db,
            """
            SELECT
                c.id,
                c.investor_id,
                c.name,
                c.budget,
                c.status,
                c.created_at,
                u.login AS investor_login,
                u.name AS investor_name
            FROM campaigns c
            JOIN users u ON u.id = c.investor_id
            ORDER BY c.id DESC
            """,
        )
    else:
        campaigns = await fetchall(
            db,
            """
            SELECT
                c.id,
                c.investor_id,
                c.name,
                c.budget,
                c.status,
                c.created_at,
                u.login AS investor_login,
                u.name AS investor_name
            FROM campaigns c
            JOIN users u ON u.id = c.investor_id
            WHERE c.investor_id = ?
            ORDER BY c.id DESC
            """,
            (int(current_user["id"]),),
        )

    return [_serialize_campaign(campaign) for campaign in campaigns]


@router.post("", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
) -> CampaignOut:
    if current_user["role"] == "admin":
        if payload.investor_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="investor_id is required for admin-created campaigns.",
            )
        investor_id = int(payload.investor_id)
        await _validate_investor(db, investor_id)
    else:
        investor_id = int(current_user["id"])

    cursor = await db.execute(
        """
        INSERT INTO campaigns (investor_id, name, budget, status, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        """,
        (investor_id, payload.name, payload.budget, payload.status),
    )
    await db.commit()

    campaign = await _fetch_campaign(db, int(cursor.lastrowid))
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load created campaign.",
        )
    return _serialize_campaign(campaign)


@router.put("/{campaign_id}", response_model=CampaignOut)
async def update_campaign(
    campaign_id: int,
    payload: CampaignUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
) -> CampaignOut:
    campaign = await _fetch_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found.",
        )

    is_owner = int(campaign["investor_id"]) == int(current_user["id"])
    if current_user["role"] != "admin" and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot manage this campaign.",
        )

    changes = payload.model_dump(exclude_unset=True)
    updates: dict[str, Any] = {}

    if "name" in changes:
        updates["name"] = changes["name"]
    if "budget" in changes:
        updates["budget"] = changes["budget"]
    if "status" in changes:
        updates["status"] = changes["status"]
    if "investor_id" in changes:
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin can reassign campaign ownership.",
            )
        if changes["investor_id"] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="investor_id cannot be null.",
            )
        new_investor_id = int(changes["investor_id"])
        await _validate_investor(db, new_investor_id)
        updates["investor_id"] = new_investor_id

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update.",
        )

    set_clause = ", ".join(f"{field} = ?" for field in updates)
    params = list(updates.values()) + [campaign_id]
    await db.execute(f"UPDATE campaigns SET {set_clause} WHERE id = ?", params)
    await db.commit()

    updated = await _fetch_campaign(db, campaign_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load updated campaign.",
        )
    return _serialize_campaign(updated)


@router.patch("/{campaign_id}/status", response_model=CampaignOut)
async def update_campaign_status(
    campaign_id: int,
    payload: CampaignStatusUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
) -> CampaignOut:
    campaign = await _fetch_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found.",
        )

    is_owner = int(campaign["investor_id"]) == int(current_user["id"])
    if current_user["role"] != "admin" and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot manage this campaign.",
        )

    await db.execute(
        "UPDATE campaigns SET status = ? WHERE id = ?",
        (payload.status, campaign_id),
    )
    await db.commit()

    updated = await _fetch_campaign(db, campaign_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load campaign.",
        )
    return _serialize_campaign(updated)


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    _: dict[str, Any] = Depends(require_roles("admin")),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any]:
    campaign = await _fetch_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found.",
        )

    # Keep deletion deterministic regardless of SQLite FK mode/version.
    deleted_apps_cursor = await db.execute(
        "DELETE FROM applications WHERE campaign_id = ?",
        (campaign_id,),
    )
    deleted_apps = int(deleted_apps_cursor.rowcount or 0)

    deleted_campaign_cursor = await db.execute(
        "DELETE FROM campaigns WHERE id = ?",
        (campaign_id,),
    )
    if int(deleted_campaign_cursor.rowcount or 0) == 0:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found.",
        )

    await db.commit()
    return {
        "success": True,
        "deleted_campaign_id": campaign_id,
        "deleted_applications": deleted_apps,
    }
