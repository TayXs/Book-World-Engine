/**
 * Watch Worth It - service worker.
 *
 * Owns the pipeline: transcript in, claims out, fact-checks looked up, channel
 * signals gathered, one score written to the cache. The content script is a
 * renderer and a same-origin fetch proxy; everything that decides anything
 * happens here, where it can be read in one file.
 */

import { extractClaims } from "./lib/claims.js";
import { checkClaims, summarizeMatches } from "./lib/factcheck.js";
import { fetchChannelSignals, mergeSignals } from "./lib/channel.js";
import { confidenceScore, band, parseCountText } from "./lib/score.js";
import { parseCaptions, pickTrack, withJson3 } from "./lib/transcript.js";
import {
  extractPlayerResponse,
  summarizePlayerResponse,
  factCheckSearchUrl,
  normalizePageSignals,
} from "./lib/ytpage.js";
import { getSettings, saveSettings, readCache, writeCache, clearCache } from "./lib/store.js";

const inFlight = new Map();

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  handle(message, sender)
    .then(sendResponse)
    .catch((error) => sendResponse({ status: "error", error: String(error?.message || error) }));
  return true; // keep the channel open for the async reply
});

async function handle(message, sender) {
  switch (message?.type) {
    case "wwi:analyze":
      return analyzeOnce(message, sender);
    case "wwi:get-settings":
      return getSettings();
    case "wwi:save-settings":
      return saveSettings(message.patch || {});
    case "wwi:open-options":
      await chrome.runtime.openOptionsPage();
      return { ok: true };
    case "wwi:clear-cache":
      await clearCache(message.videoId);
      return { ok: true };
    default:
      throw new Error(`unknown message: ${message?.type}`);
  }
}

/** One analysis per video at a time; a second panel open just joins the first. */
function analyzeOnce(message, sender) {
  const tabId = sender?.tab?.id;
  const key = `${tabId}:${message.videoId}:${message.force ? Date.now() : ""}`;
  if (inFlight.has(key)) return inFlight.get(key);
  const promise = analyze(message, tabId).finally(() => inFlight.delete(key));
  inFlight.set(key, promise);
  return promise;
}

async function analyze({ videoId, pageSignals = {}, force = false }, tabId) {
  if (!videoId) throw new Error("no video id");
  const settings = await getSettings();

  if (!force) {
    const cached = await readCache(videoId);
    if (cached) return { ...cached, fromCache: true };
  }

  const warnings = [];
  const player = await readPlayer(tabId, videoId).catch((error) => {
    warnings.push(`Could not read the player: ${error.message}`);
    return null;
  });

  const title = player?.title || pageSignals.title || "";
  const channelTitle = player?.author || pageSignals.channelTitle || "";
  const searchUrl = factCheckSearchUrl(title, channelTitle);

  const base = {
    videoId,
    title,
    channelTitle,
    searchUrl,
    tier: "free",
    generatedAt: new Date().toISOString(),
  };

  const cues = await readTranscript(tabId, player).catch((error) => {
    warnings.push(`Transcript fetch failed: ${error.message}`);
    return [];
  });

  if (cues.length === 0) {
    // Nothing to extract claims from. Channel signals are still worth showing.
    const channel = await gatherChannelSignals(videoId, pageSignals, settings, warnings);
    return writeCache(videoId, {
      ...base,
      status: "no-transcript",
      score: null,
      band: "unverified",
      unverified: true,
      reason: "No captions are available for this video, so there is nothing to check.",
      claims: [],
      channel: confidenceScore({ factCheck: null, channel }).channel,
      channelSignals: channel,
      warnings,
    });
  }

  const claims = extractClaims(cues, { max: settings.maxClaims });

  let results = [];
  if (!settings.factCheckApiKey) {
    warnings.push("No Fact Check API key set - add one in options to look claims up.");
  } else if (claims.length > 0) {
    results = await checkClaims(claims, { apiKey: settings.factCheckApiKey });
    const failed = results.find((r) => r.error);
    if (failed) warnings.push(`Fact Check API: ${failed.error}`);
  }

  const summary = summarizeMatches(results);
  const channel = await gatherChannelSignals(videoId, pageSignals, settings, warnings);
  const scored = confidenceScore({ factCheck: summary, channel });

  return writeCache(videoId, {
    ...base,
    status: "ok",
    score: scored.score,
    band: band(scored.score),
    unverified: scored.unverified,
    reason: scored.reason || "",
    claims: claims.map((claim, index) => ({
      ...claim,
      matches: results[index]?.matches || [],
      error: results[index]?.error || "",
    })),
    factCheck: scored.factCheck,
    channel: scored.channel,
    channelSignals: channel,
    transcript: { cues: cues.length, characters: cues.reduce((n, c) => n + c.text.length, 0) },
    warnings,
  });
}

/* ------------------------------------------------------------------ transcript */

/**
 * The live player response first - it is already in memory. It goes stale on
 * SPA navigation, so the video id is verified before it is trusted, and the
 * served HTML is the fallback.
 */
async function readPlayer(tabId, videoId) {
  if (tabId !== undefined && tabId !== null) {
    try {
      const [injected] = await chrome.scripting.executeScript({
        target: { tabId },
        world: "MAIN",
        func: readPlayerResponseInPage,
      });
      const live = injected?.result;
      if (live && live.videoId === videoId && live.tracks?.length) return live;
    } catch {
      // Injection is blocked on some pages; the HTML path below still works.
    }
  }

  const html = await fetchViaTab(tabId, `https://www.youtube.com/watch?v=${videoId}&hl=en`);
  const summary = summarizePlayerResponse(extractPlayerResponse(html));
  if (!summary) throw new Error("no player response in the page");
  return summary;
}

/**
 * Runs in the page's own world, so it must stand alone - no imports, no
 * closures. Summarizing here keeps a megabyte of player JSON out of the
 * message channel.
 */
function readPlayerResponseInPage() {
  try {
    let response = window.ytInitialPlayerResponse;
    if (!response && window.ytplayer?.config?.args?.player_response) {
      response = JSON.parse(window.ytplayer.config.args.player_response);
    }
    if (!response) return null;
    const details = response.videoDetails || {};
    const tracks = response.captions?.playerCaptionsTracklistRenderer?.captionTracks || [];
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
          name: track.name?.simpleText || "",
        })),
    };
  } catch {
    return null;
  }
}

async function readTranscript(tabId, player) {
  const track = pickTrack(player?.tracks || []);
  if (!track) return [];

  let cues = parseCaptions(await fetchViaTab(tabId, withJson3(track.baseUrl)));
  if (cues.length === 0) {
    // json3 is occasionally refused; the XML form usually still answers.
    cues = parseCaptions(await fetchViaTab(tabId, track.baseUrl));
  }
  return cues;
}

/**
 * YouTube URLs are fetched by the content script, not here: in the tab they are
 * same-origin and carry the session, which is what keeps the caption endpoint
 * answering.
 */
async function fetchViaTab(tabId, url) {
  if (tabId === undefined || tabId === null) throw new Error("no tab to fetch from");
  const response = await chrome.tabs.sendMessage(tabId, { type: "wwi:fetch", url });
  if (!response?.ok) throw new Error(response?.error || `HTTP ${response?.status ?? "?"}`);
  return response.body;
}

/* ------------------------------------------------------------------- channel */

async function gatherChannelSignals(videoId, pageSignals, settings, warnings) {
  // What the watch page says is the floor: it needs no key and no quota.
  const fromPage = normalizePageSignals(pageSignals, Date.now(), parseCountText);
  const credentials = { apiKey: settings.youtubeApiKey };
  if (!credentials.apiKey) return mergeSignals(fromPage, { available: false });

  try {
    const api = await fetchChannelSignals(videoId, credentials);
    return mergeSignals(fromPage, api);
  } catch (error) {
    warnings.push(`YouTube Data API: ${error.message}`);
    return mergeSignals(fromPage, { available: false });
  }
}

chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") chrome.runtime.openOptionsPage();
});
