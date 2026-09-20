/**
 * Reading the watch page itself. Two ways in, because neither is reliable alone:
 * the live `ytInitialPlayerResponse` (fast, but stale after an SPA navigation)
 * and the served HTML (always current, sometimes behind a consent wall).
 */

/** Video id out of any of the URL shapes YouTube uses. */
export function videoIdFromUrl(url) {
  if (!url) return null;
  let parsed;
  try {
    parsed = new URL(url, "https://www.youtube.com");
  } catch {
    return null;
  }
  const id = parsed.searchParams.get("v");
  if (id && /^[A-Za-z0-9_-]{11}$/.test(id)) return id;
  const path = /\/(?:shorts|embed|live|v)\/([A-Za-z0-9_-]{11})/.exec(parsed.pathname);
  if (path) return path[1];
  if (parsed.hostname.endsWith("youtu.be")) {
    const short = /^\/([A-Za-z0-9_-]{11})/.exec(parsed.pathname);
    if (short) return short[1];
  }
  return null;
}

/**
 * Pull the JSON object that follows `ytInitialPlayerResponse =` out of the page
 * HTML by matching braces - a lazy regex stops at the first `}` inside a caption
 * title and hands back something unparseable.
 */
export function extractPlayerResponse(html) {
  if (typeof html !== "string") return null;
  const marker = /ytInitialPlayerResponse\s*=\s*\{/.exec(html);
  if (!marker) return null;

  const start = marker.index + marker[0].length - 1;
  let depth = 0;
  let inString = false;
  let escaped = false;

  for (let i = start; i < html.length; i++) {
    const char = html[i];
    if (inString) {
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === '"') inString = false;
      continue;
    }
    if (char === '"') inString = true;
    else if (char === "{") depth++;
    else if (char === "}") {
      depth--;
      if (depth === 0) {
        try {
          return JSON.parse(html.slice(start, i + 1));
        } catch {
          return null;
        }
      }
    }
  }
  return null;
}

/** The bits of a player response we care about, in our own shape. */
export function summarizePlayerResponse(playerResponse) {
  if (!playerResponse) return null;
  const details = playerResponse.videoDetails || {};
  const tracks =
    playerResponse.captions?.playerCaptionsTracklistRenderer?.captionTracks || [];
  return {
    videoId: details.videoId || null,
    title: details.title || "",
    author: details.author || "",
    channelId: details.channelId || "",
    lengthSeconds: Number(details.lengthSeconds) || null,
    tracks: tracks
      .filter((track) => track && track.baseUrl)
      .map((track) => ({
        baseUrl: track.baseUrl,
        languageCode: track.languageCode || "",
        kind: track.kind || "",
        name: track.name?.simpleText || track.name?.runs?.[0]?.text || "",
      })),
  };
}

/** A manual next step when the fact-check index has nothing: just search. */
export function factCheckSearchUrl(title, channelTitle) {
  const topic = [title, channelTitle].filter(Boolean).join(" ").slice(0, 180);
  return `https://www.google.com/search?q=${encodeURIComponent(`${topic} fact check`)}`;
}

const RELATIVE_UNITS = {
  second: 1 / 86400,
  minute: 1 / 1440,
  hour: 1 / 24,
  day: 1,
  week: 7,
  month: 30.44,
  year: 365.25,
};

/**
 * The date line under a video, as the page writes it: "3 weeks ago",
 * "Premiered Sep 12, 2026", "Streamed live on 4 Jan 2024". Returns ISO or null.
 */
export function parseWatchDate(text, now = Date.now()) {
  if (!text) return null;
  const cleaned = String(text)
    .replace(/^(?:premiered|streamed live on|started streaming on|uploaded on)\s+/i, "")
    .trim();

  const relative = /(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago/i.exec(cleaned);
  if (relative) {
    const days = Number(relative[1]) * RELATIVE_UNITS[relative[2].toLowerCase()];
    return new Date(now - days * 86400000).toISOString();
  }

  const absolute = Date.parse(cleaned);
  if (!Number.isNaN(absolute)) return new Date(absolute).toISOString();
  return null;
}

/** The page's own numbers, turned into the fields the scorer expects. */
export function normalizePageSignals(pageSignals = {}, now = Date.now(), parseCount = null) {
  const normalized = {
    title: pageSignals.title || "",
    channelTitle: pageSignals.channelTitle || "",
  };
  const published = parseWatchDate(pageSignals.dateText, now);
  if (published) normalized.publishedAt = published;
  if (parseCount) {
    const subscribers = parseCount(pageSignals.subscriberText);
    if (subscribers) normalized.subscriberCount = subscribers;
    const views = parseCount(pageSignals.viewText);
    if (views) normalized.viewCount = views;
  }
  return normalized;
}
