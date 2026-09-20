/**
 * Channel-level signals from the YouTube Data API - the same free quota that
 * backs "Connect YouTube", and happy with a plain API key when it isn't.
 *
 * If neither is configured we fall back to what the watch page already shows,
 * so the default tier still has something to say without any setup at all.
 */

const BASE = "https://www.googleapis.com/youtube/v3";

function authorize(url, { apiKey, token }) {
  const headers = { Accept: "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  else if (apiKey) url.searchParams.set("key", apiKey);
  return { url, headers };
}

async function getJson(path, params, credentials, fetchImpl = fetch) {
  const url = new URL(`${BASE}/${path}`);
  for (const [key, value] of Object.entries(params)) url.searchParams.set(key, value);
  const request = authorize(url, credentials);
  const response = await fetchImpl(request.url.toString(), { headers: request.headers });
  if (!response.ok) {
    throw new Error(`YouTube Data API ${path}: HTTP ${response.status}`);
  }
  return response.json();
}

/** Uploads per month over the recent run of videos, not over all time. */
export function uploadsPerMonth(dates, now = Date.now()) {
  const times = (dates || [])
    .map((d) => Date.parse(d))
    .filter((t) => !Number.isNaN(t))
    .sort((a, b) => b - a);
  if (times.length < 2) return null;
  const spanDays = (times[0] - times[times.length - 1]) / 86400000;
  if (spanDays <= 0) return null;
  return ((times.length - 1) / spanDays) * 30.4;
}

/**
 * Three cheap calls: the video, its channel, and the tail of the uploads
 * playlist. Any of them may fail on quota or a hidden subscriber count; the
 * caller gets whatever came back.
 */
export async function fetchChannelSignals(videoId, credentials = {}, fetchImpl = fetch) {
  if (!credentials.apiKey && !credentials.token) {
    return { available: false, reason: "no-credentials" };
  }

  const video = await getJson(
    "videos",
    { part: "snippet,statistics", id: videoId },
    credentials,
    fetchImpl
  );
  const item = video?.items?.[0];
  if (!item) return { available: false, reason: "video-not-found" };

  const signals = {
    available: true,
    title: item.snippet?.title || "",
    channelTitle: item.snippet?.channelTitle || "",
    channelId: item.snippet?.channelId || "",
    publishedAt: item.snippet?.publishedAt || "",
    viewCount: Number(item.statistics?.viewCount) || null,
  };

  if (!signals.channelId) return signals;

  try {
    const channel = await getJson(
      "channels",
      { part: "snippet,statistics,contentDetails", id: signals.channelId },
      credentials,
      fetchImpl
    );
    const channelItem = channel?.items?.[0];
    if (channelItem) {
      signals.channelPublishedAt = channelItem.snippet?.publishedAt || "";
      signals.subscriberCount = channelItem.statistics?.hiddenSubscriberCount
        ? null
        : Number(channelItem.statistics?.subscriberCount) || null;
      signals.videoCount = Number(channelItem.statistics?.videoCount) || null;
      const uploads = channelItem.contentDetails?.relatedPlaylists?.uploads;
      if (uploads) {
        const playlist = await getJson(
          "playlistItems",
          { part: "snippet", playlistId: uploads, maxResults: "15" },
          credentials,
          fetchImpl
        );
        const dates = (playlist?.items || []).map((i) => i.snippet?.publishedAt);
        signals.uploadsPerMonth = uploadsPerMonth(dates);
      }
    }
  } catch (error) {
    signals.channelError = String(error?.message || error);
  }

  return signals;
}

/**
 * Merge whatever the page already told us with whatever the API returned. The
 * API wins where both have an answer; the page fills the rest.
 */
export function mergeSignals(pageSignals = {}, apiSignals = {}) {
  const merged = { ...pageSignals };
  for (const [key, value] of Object.entries(apiSignals)) {
    if (value !== null && value !== undefined && value !== "") merged[key] = value;
  }
  merged.source = apiSignals.available ? "youtube-data-api" : "watch-page";
  return merged;
}
