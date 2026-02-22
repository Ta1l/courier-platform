// Configuration - change BOT_LINK before deployment
export const CONFIG = {
  BOT_LINK: "https://t.me/kurer_pro_bot?start=",
  GA4_MEASUREMENT_ID: "G-XXXXXXXXXX",
  YANDEX_METRIKA_ID: "XXXXXXXX",
  DEFAULT_UTM_SOURCE: "pub",
  CONTACT_EMAIL: "placeholder@example.com",
};

function getCampaignPayload(params: URLSearchParams): string | null {
  const rawCampaign = params.get("camp")?.trim();
  if (!rawCampaign) return null;
  if (!/^\d+$/.test(rawCampaign)) return null;
  return `camp_${rawCampaign}`;
}

function getDefaultSource(params: URLSearchParams, customSource?: string): string {
  return customSource || params.get("utm_source") || params.get("start") || CONFIG.DEFAULT_UTM_SOURCE;
}

export function getStartPayload(customSource?: string): string {
  const params = new URLSearchParams(window.location.search);
  const campaignPayload = getCampaignPayload(params);
  if (campaignPayload) {
    return campaignPayload;
  }
  return getDefaultSource(params, customSource);
}

/**
 * Get the bot link with source/start payload appended.
 * If ?camp=<id> is present, payload becomes camp_<id>.
 */
export function getBotLink(customSource?: string): string {
  return `${CONFIG.BOT_LINK}${encodeURIComponent(getStartPayload(customSource))}`;
}

export function getBotLinkCard(): string {
  const params = new URLSearchParams(window.location.search);
  const campaignPayload = getCampaignPayload(params);
  if (campaignPayload) {
    return `${CONFIG.BOT_LINK}${encodeURIComponent(campaignPayload)}`;
  }
  const source = getDefaultSource(params);
  return `${CONFIG.BOT_LINK}${encodeURIComponent(`card_${source}`)}`;
}
