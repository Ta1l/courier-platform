"""Pydantic schemas for admin API."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

RoleType = Literal["admin", "investor"]
CampaignStatusType = Literal["active", "paused"]
ApplicationStatusType = Literal["new", "in_progress", "approved", "rejected"]


class LoginRequest(BaseModel):
    login: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class UserOut(BaseModel):
    id: int
    login: str
    name: str
    role: RoleType
    percent: float | None
    is_active: bool
    created_at: str


class UserCreate(BaseModel):
    login: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=120)
    role: RoleType
    percent: float | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def validate_percent(self) -> "UserCreate":
        if self.role == "investor" and self.percent is None:
            raise ValueError("percent is required for investor role")
        if self.role == "admin":
            self.percent = None
        return self


class UserUpdate(BaseModel):
    login: str | None = Field(default=None, min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str | None = Field(default=None, min_length=8, max_length=128)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    role: RoleType | None = None
    percent: float | None = Field(default=None, ge=0, le=100)


class UserToggleResponse(BaseModel):
    success: bool
    user: UserOut


class CampaignOut(BaseModel):
    id: int
    investor_id: int
    investor_login: str | None = None
    investor_name: str | None = None
    name: str
    budget: float
    status: CampaignStatusType
    created_at: str


class CampaignCreate(BaseModel):
    investor_id: int | None = None
    name: str = Field(min_length=1, max_length=255)
    budget: float = Field(ge=0)
    status: CampaignStatusType = "active"


class CampaignUpdate(BaseModel):
    investor_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    budget: float | None = Field(default=None, ge=0)
    status: CampaignStatusType | None = None


class CampaignStatusUpdate(BaseModel):
    status: CampaignStatusType


class ApplicationOut(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    phone: str
    age: int
    citizenship: str
    source: str | None
    contacted: bool
    submitted_at: str
    campaign_id: int | None
    campaign_name: str | None
    status: str | None
    revenue: float | None


class ApplicationUpdate(BaseModel):
    status: ApplicationStatusType | None = None
    revenue: float | None = Field(default=None, ge=0)


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class TimelinePoint(BaseModel):
    date: str
    revenue: float


class CampaignMetric(BaseModel):
    campaign_id: int
    campaign_name: str
    investor_id: int
    investor_name: str | None
    status: str
    budget: float
    percent: float
    applications_count: int
    total_revenue: float
    net_profit: float
    investor_profit: float
    admin_profit: float
    roi: float


class DashboardTotals(BaseModel):
    campaigns: int
    total_budget: float
    total_revenue: float
    net_profit: float
    investor_profit: float
    admin_profit: float
    roi: float


class DashboardResponse(BaseModel):
    totals: DashboardTotals
    campaigns: list[CampaignMetric]
    timeline: list[TimelinePoint]
    generated_at: str


class CampaignStatsResponse(BaseModel):
    campaign: CampaignMetric
    applications_by_status: dict[str, int]
    timeline: list[TimelinePoint]
    generated_at: str


class ApplicationFilters(BaseModel):
    campaign: int | None = None
    status: str | None = None
    date_from: date | None = None
    date_to: date | None = None

