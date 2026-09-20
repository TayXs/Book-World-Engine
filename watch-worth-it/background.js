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
    case "wwi:connect-youtube": {
      const { connect } = await import("./lib/auth.js");
      await connect();
      return saveSettings({ youtubeConnected: true });
    }
    case "wwi:disconnect-youtube": {
      const { disconnect } = await import("./lib/auth.js");
      const result = await disconnect();
      return { ...(await saveSettings({ youtubeConnected: false })), ...result };
    }
    case "wwi:test-key": {
      const { testFactCheckKey, testYouTubeKey } = await import("./lib/keytest.js");
      return message.which === "youtube"
        ? testYouTubeKey(message.apiKey)
        : testFactCheckKey(message.apiKey);
    }
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

async function analyze({ videoId, pageSignals = {}, force = false, origin }, tabId) {
  if (!videoId) throw new Error("no video id");
  const settings = await getSettings();

  if (!force) {
    const cached = await readCache(videoId);
    if (cached) return { ...cached, fromCache: true };
  }

  const warnings = [];
  let failure = null;
  const player = await readPlayer(tabId, videoId, origin).catch((error) => {
    failure = `Could not read this page's caption list (${error.message}).`;
    warnings.push(failure);
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
    failure = failure || `The caption track could not be fetched (${error.message}).`;
    warnings.push(failure);
    return [];
  });

  if (cues.length === 0) {
    // Nothing to extract claims from. Channel signals are still worth showing.
    const channel = await gatherChannelSignals(videoId, pageSignals, settings, warnings);
    const result = {
      ...base,
      status: "no-transcript",
      transient: Boolean(failure),
      score: null,
      band: "unverified",
      unverified: true,
      reason: failure || "No captions are available for this video, so there is nothing to check.",
      claims: [],
      channel: confidenceScore({ factCheck: null, channel }).channel,
      channelSignals: channel,
      warnings,
    };
    // A video that genuinely has no captions will have none tomorrow either. A
    // page we simply could not read is worth retrying, so it is not cached.
    return failure ? result : writeCache(videoId, result);
  }

  // The AI tier replaces claim extraction and nothing else: whatever it returns
  // goes through the same lookup and the same scoring rule below. It is loaded
  // only when the toggle is on, so the free path never even imports it.
  let claims = [];
  let ai = null;
  let tier = "free";
  if (settings.aiEnabled && settings.aiApiKey) {
    try {
      const { runAiTier } = await import("./lib/ai.js");
      ai = await runAiTier({ cues, title, channelTitle, settings });
      claims = ai.claims;
      tier = "ai";
      if (ai.transcriptTrimmed) {
        warnings.push("Transcript was long - only the first 48,000 characters went to the model.");
      }
      const unlocated = claims.filter((claim) => !claim.located).length;
      if (unlocated > 0) {
        warnings.push(`${unlocated} AI claim(s) could not be found in the transcript; their timestamps are missing.`);
      }
    } catch (error) {
      warnings.push(`AI tier failed (${error.message}) - fell back to the free heuristics.`);
    }
  } else if (settings.aiEnabled) {
    warnings.push("AI tier is on but no API key is set.");
  }
  if (claims.length === 0) claims = extractClaims(cues, { max: settings.maxClaims });

  // checkClaims makes no request without a key: it marks every claim skipped,
  // which is what lets the panel say "not looked up" rather than "not found".
  const results = claims.length > 0 ? await checkClaims(claims, { apiKey: settings.factCheckApiKey }) : [];
  if (!settings.factCheckApiKey) {
    warnings.push("No Fact Check API key set - add one in options to look claims up.");
  } else {
    const failed = results.find((r) => r.error);
    if (failed) warnings.push(`Fact Check API: ${failed.error}`);
  }

  const summary = summarizeMatches(results);
  const channel = await gatherChannelSignals(videoId, pageSignals, settings, warnings);
  const scored = confidenceScore({ factCheck: summary, channel });

  return writeCache(videoId, {
    ...base,
    tier,
    ai: ai
      ? { summary: ai.summary, caveats: ai.caveats, provider: ai.provider, model: ai.model }
      : null,
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
async function readPlayer(tabId, videoId, origin) {
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

  // Same host as the tab: fetching www from an m.youtube.com page is a
  // cross-origin round trip we do not need to make.
  const host = origin === "https://m.youtube.com" ? origin : "https://www.youtube.com";
  const html = await fetchViaTab(tabId, `${host}/watch?v=${videoId}&hl=en`);
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
  if (tabId !== undefined && tabId !== null) {
    try {
      const response = await chrome.tabs.sendMessage(tabId, { type: "wwi:fetch", url });
      if (response?.ok) return response.body;
      // A cross-origin url (mobile YouTube asking for a www.youtube.com caption
      // track) is the worker's job, not the page's. So is a dead content script.
      if (!response?.crossOrigin && response?.status) {
        throw new Error(response.error || `HTTP ${response.status}`);
      }
    } catch (error) {
      if (!/Receiving end does not exist|message port closed/i.test(String(error?.message))) {
        if (!/cross-origin/i.test(String(error?.message))) throw error;
      }
    }
  }
  return fetchDirect(url);
}

/**
 * The worker holds the host permissions, so it can fetch either YouTube origin.
 * It is the fallback rather than the default because a request from the tab is
 * same-origin and carries the session, which the caption endpoint prefers.
 */
async function fetchDirect(url) {
  const response = await fetch(url, { credentials: "include" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.text();
}

/* ------------------------------------------------------------------- channel */

async function gatherChannelSignals(videoId, pageSignals, settings, warnings) {
  // What the watch page says is the floor: it needs no key and no quota.
  const fromPage = normalizePageSignals(pageSignals, Date.now(), parseCountText);
  const credentials = { apiKey: settings.youtubeApiKey };
  if (!credentials.apiKey && settings.youtubeConnected) {
    // A connected account is used for one thing: public channel statistics on
    // the free quota, as an alternative to pasting a key.
    const { getToken } = await import("./lib/auth.js");
    credentials.token = await getToken({ interactive: false });
  }
  if (!credentials.apiKey && !credentials.token) return mergeSignals(fromPage, { available: false });

  try {
    const api = await fetchChannelSignals(videoId, credentials);
    return mergeSignals(fromPage, api);
  } catch (error) {
    warnings.push(`YouTube Data API: ${error.message}`);
    return mergeSignals(fromPage, { available: false });
  }
}

chrome.action.onClicked.addListener(() => chrome.runtime.openOptionsPage());

chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") chrome.runtime.openOptionsPage();
});
