// Configuration - change BOT_LINK before deployment
export const CONFIG = {
  BOT_LINK: "https://t.me/kurer_pro_bot?start=",
  GA4_MEASUREMENT_ID: "G-XXXXXXXXXX",
  YANDEX_METRIKA_ID: "XXXXXXXX",
  DEFAULT_UTM_SOURCE: "pub",
  CONTACT_EMAIL: "placeholder@example.com",
};

function normalizeCampaignId(raw: string | null | undefined): string | null {
  const value = raw?.trim();
  if (!value) return null;
  if (!/^\d+$/.test(value)) return null;
  return value;
}

function getCampaignIdFromPathname(pathname: string): string | null {
  const match = pathname.match(/^\/camp\/(\d+)\/?$/);
  return match?.[1] ?? null;
}

function resolveCampaignId(campIdFromPath?: string): string | null {
  const fromRouteParam = normalizeCampaignId(campIdFromPath);
  if (fromRouteParam) return fromRouteParam;

  const fromPathname = getCampaignIdFromPathname(window.location.pathname);
  if (fromPathname) return fromPathname;

  const params = new URLSearchParams(window.location.search);
  return normalizeCampaignId(params.get("camp"));
}

function getCampaignPayload(campIdFromPath?: string): string | null {
  const campaignId = resolveCampaignId(campIdFromPath);
  if (!campaignId) return null;
  return `camp_${campaignId}`;
}

function getDefaultSource(params: URLSearchParams, customSource?: string): string {
  return customSource || params.get("utm_source") || params.get("start") || CONFIG.DEFAULT_UTM_SOURCE;
}

export function getStartPayload(customSource?: string, campIdFromPath?: string): string {
  const params = new URLSearchParams(window.location.search);
  const campaignPayload = getCampaignPayload(campIdFromPath);
  if (campaignPayload) {
    return campaignPayload;
  }
  return getDefaultSource(params, customSource);
}

/**
 * Get the bot link with source/start payload appended.
 * If /camp/<id> or ?camp=<id> is present, payload becomes camp_<id>.
 */
export function getBotLink(customSource?: string, campIdFromPath?: string): string {
  return `${CONFIG.BOT_LINK}${encodeURIComponent(getStartPayload(customSource, campIdFromPath))}`;
}

export function getBotLinkCard(campIdFromPath?: string): string {
  const params = new URLSearchParams(window.location.search);
  const campaignPayload = getCampaignPayload(campIdFromPath);
  if (campaignPayload) {
    return `${CONFIG.BOT_LINK}${encodeURIComponent(campaignPayload)}`;
  }
  const source = getDefaultSource(params);
  return `${CONFIG.BOT_LINK}${encodeURIComponent(`card_${source}`)}`;
}
