/** Settings and the per-video result cache, both in chrome.storage.local. */

const SETTINGS_KEY = "wwi:settings";
const CACHE_PREFIX = "wwi:v1:";
const CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000;
const CACHE_LIMIT = 200;

export const DEFAULT_SETTINGS = {
  factCheckApiKey: "",
  youtubeApiKey: "",
  maxClaims: 10,
  autoRun: true,
  // Everything below is opt-in and off by default. The free tier never reads it.
  youtubeConnected: false,
  aiEnabled: false,
  aiProvider: "gemini", // gemini | anthropic | openai
  aiApiKey: "",
  aiModel: "",
};

export async function getSettings() {
  const stored = await chrome.storage.local.get(SETTINGS_KEY);
  return { ...DEFAULT_SETTINGS, ...(stored[SETTINGS_KEY] || {}) };
}

export async function saveSettings(patch) {
  const next = { ...(await getSettings()), ...patch };
  await chrome.storage.local.set({ [SETTINGS_KEY]: next });
  return next;
}

const cacheKey = (videoId) => `${CACHE_PREFIX}${videoId}`;

export async function readCache(videoId) {
  const key = cacheKey(videoId);
  const stored = await chrome.storage.local.get(key);
  const entry = stored[key];
  if (!entry) return null;
  if (Date.now() - (entry.cachedAt || 0) > CACHE_TTL_MS) {
    await chrome.storage.local.remove(key);
    return null;
  }
  return entry;
}

export async function writeCache(videoId, result) {
  const entry = { ...result, cachedAt: Date.now() };
  await chrome.storage.local.set({ [cacheKey(videoId)]: entry });
  await pruneCache();
  return entry;
}

export async function clearCache(videoId) {
  if (videoId) return chrome.storage.local.remove(cacheKey(videoId));
  const all = await chrome.storage.local.get(null);
  const keys = Object.keys(all).filter((k) => k.startsWith(CACHE_PREFIX));
  if (keys.length) await chrome.storage.local.remove(keys);
}

/** Oldest out first - the cache is a convenience, never a record. */
async function pruneCache() {
  const all = await chrome.storage.local.get(null);
  const entries = Object.entries(all)
    .filter(([key]) => key.startsWith(CACHE_PREFIX))
    .sort((a, b) => (a[1]?.cachedAt || 0) - (b[1]?.cachedAt || 0));
  if (entries.length <= CACHE_LIMIT) return;
  const excess = entries.slice(0, entries.length - CACHE_LIMIT).map(([key]) => key);
  await chrome.storage.local.remove(excess);
}

export { CACHE_PREFIX, CACHE_TTL_MS, SETTINGS_KEY };
