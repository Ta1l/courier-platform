export type Role = "admin" | "investor";

export type User = {
  id: number;
  login: string;
  name: string;
  role: Role;
  percent: number | null;
  is_active: boolean;
  created_at: string;
};

export type Campaign = {
  id: number;
  investor_id: number;
  investor_login: string | null;
  investor_name: string | null;
  name: string;
  budget: number;
  status: "active" | "paused";
  created_at: string;
};

export type Application = {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  phone: string;
  age: number;
  citizenship: string;
  source: string | null;
  contacted: boolean;
  submitted_at: string;
  campaign_id: number | null;
  campaign_name: string | null;
  status: string | null;
  revenue: number | null;
};

export type DashboardTotals = {
  campaigns: number;
  total_budget: number;
  total_revenue: number;
  net_profit: number;
  investor_profit: number;
  admin_profit: number;
  roi: number;
};

export type CampaignMetric = {
  campaign_id: number;
  campaign_name: string;
  investor_id: number;
  investor_name: string | null;
  status: string;
  budget: number;
  percent: number;
  applications_count: number;
  total_revenue: number;
  net_profit: number;
  investor_profit: number;
  admin_profit: number;
  roi: number;
};

export type TimelinePoint = {
  date: string;
  revenue: number;
};

export type DashboardResponse = {
  totals: DashboardTotals;
  campaigns: CampaignMetric[];
  timeline: TimelinePoint[];
  generated_at: string;
};

export type AuthResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
};
