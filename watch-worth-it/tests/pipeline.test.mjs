/**
 * The whole service worker, driven through its real message listener with
 * chrome.* and fetch stubbed. This is the test that would have caught a broken
 * wire between two modules that each pass their own tests.
 */
import test from "node:test";
import assert from "node:assert/strict";

/* ------------------------------------------------------------- the fixtures */

const VIDEO_ID = "abc12345678";
const TRACK_URL = "https://www.youtube.com/api/timedtext?v=abc12345678&lang=en&signature=xyz";

const PLAYER_RESPONSE = {
  videoDetails: { videoId: VIDEO_ID, title: "Are eggs getting pricier?", author: "Food Desk", lengthSeconds: "600" },
  captions: {
    playerCaptionsTracklistRenderer: {
      captionTracks: [{ baseUrl: TRACK_URL, languageCode: "en", kind: "", name: { simpleText: "English" } }],
    },
  },
};

const CAPTIONS = {
  events: [
    { tStartMs: 0, dDurationMs: 4000, segs: [{ utf8: "Welcome back, and please smash that subscribe button." }] },
    {
      tStartMs: 5000,
      dDurationMs: 6000,
      segs: [{ utf8: "Egg prices rose 12 percent last year, according to the Department of Agriculture." }],
    },
    { tStartMs: 12000, dDurationMs: 4000, segs: [{ utf8: "I think they might keep climbing, maybe." }] },
    {
      tStartMs: 20000,
      dDurationMs: 6000,
      segs: [{ utf8: "A 2019 Harvard study found coffee drinkers had a 15 percent lower risk of heart disease." }],
    },
  ],
};

const FACT_CHECK = {
  claims: [
    {
      text: "Egg prices rose 12 percent last year according to the Department of Agriculture",
      claimant: "Food Desk",
      claimReview: [
        {
          publisher: { name: "FactCheck.example" },
          url: "https://factcheck.example/eggs",
          title: "Egg prices",
          textualRating: "Mostly True",
          reviewDate: "2026-03-01",
        },
      ],
    },
  ],
};

/* ----------------------------------------------------------------- the stubs */

/**
 * background.js registers its listener once, on import, so the harness is set
 * up once too: tests change how the stubs behave rather than replacing them.
 */
const config = { livePlayer: false, serveCaptions: true, tabFails: false, aiResponse: null, aiFails: false };
const calls = { tabFetches: [], apiFetches: [], executeScript: 0 };

function fakeStorage() {
  const data = new Map();
  return {
    async get(keys) {
      if (keys === null || keys === undefined) return Object.fromEntries(data);
      const list = Array.isArray(keys) ? keys : [keys];
      const out = {};
      for (const key of list) if (data.has(key)) out[key] = data.get(key);
      return out;
    },
    async set(items) {
      for (const [key, value] of Object.entries(items)) data.set(key, value);
    },
    async remove(keys) {
      for (const key of Array.isArray(keys) ? keys : [keys]) data.delete(key);
    },
    _data: data,
  };
}

let storage = fakeStorage();
let onMessage = null;

globalThis.chrome = {
  runtime: {
    onMessage: { addListener: (fn) => (onMessage = fn) },
    onInstalled: { addListener: () => {} },
    openOptionsPage: async () => {},
  },
  action: { onClicked: { addListener: () => {} } },
  storage: { local: { get: (k) => storage.get(k), set: (i) => storage.set(i), remove: (k) => storage.remove(k) } },
  scripting: {
    executeScript: async () => {
      calls.executeScript += 1;
      if (!config.livePlayer) return [{ result: null }];
      return [
        {
          result: {
            videoId: VIDEO_ID,
            title: PLAYER_RESPONSE.videoDetails.title,
            author: PLAYER_RESPONSE.videoDetails.author,
            tracks: [{ baseUrl: TRACK_URL, languageCode: "en", kind: "" }],
          },
        },
      ];
    },
  },
  tabs: {
    sendMessage: async (_tabId, message) => {
      calls.tabFetches.push(message.url);
      if (config.tabFails) return { ok: false, status: 500, error: "HTTP 500" };
      if (message.url.includes("/watch?v=")) {
        return {
          ok: true,
          status: 200,
          body: `<script>var ytInitialPlayerResponse = ${JSON.stringify(PLAYER_RESPONSE)};</script>`,
        };
      }
      if (message.url.includes("timedtext")) {
        return config.serveCaptions
          ? { ok: true, status: 200, body: JSON.stringify(CAPTIONS) }
          : { ok: true, status: 200, body: "" };
      }
      return { ok: false, status: 404, error: "HTTP 404" };
    },
  },
};

globalThis.fetch = async (url) => {
  calls.apiFetches.push(String(url));
  if (String(url).includes("factchecktools.googleapis.com")) {
    return { ok: true, status: 200, json: async () => FACT_CHECK };
  }
  if (String(url).includes("generativelanguage.googleapis.com")) {
    if (config.aiFails) {
      return { ok: false, status: 429, json: async () => ({ error: { message: "quota exhausted" } }) };
    }
    return {
      ok: true,
      status: 200,
      json: async () => ({ candidates: [{ content: { parts: [{ text: JSON.stringify(config.aiResponse) }] } }] }),
    };
  }
  throw new Error(`unexpected fetch: ${url}`);
};

const send = (message) =>
  new Promise((resolve, reject) => {
    const kept = onMessage(message, { tab: { id: 7 } }, resolve);
    if (kept !== true) reject(new Error("the listener must keep the channel open"));
  });

/** Back to a clean slate between tests: empty storage, default behaviour. */
async function reset(patch = {}) {
  storage = fakeStorage();
  Object.assign(config, { livePlayer: false, serveCaptions: true, tabFails: false, aiFails: false, aiResponse: null });
  calls.tabFetches.length = 0;
  calls.apiFetches.length = 0;
  calls.executeScript = 0;
  await send({ type: "wwi:save-settings", patch: { factCheckApiKey: "fc-key", ...patch } });
}

/* ----------------------------------------------------------------- the tests */

await import("../background.js");
assert.ok(onMessage, "background.js registers its message listener on import");

test("a watch page becomes a score, through every module in turn", async () => {
  await reset();
  const result = await send({
    type: "wwi:analyze",
    videoId: VIDEO_ID,
    pageSignals: { title: "Are eggs getting pricier?", subscriberText: "1.2M subscribers", dateText: "3 weeks ago" },
  });

  assert.equal(result.status, "ok");
  assert.equal(result.tier, "free");
  assert.equal(result.title, "Are eggs getting pricier?");
  assert.equal(result.channelTitle, "Food Desk");

  // Boilerplate and the hedged sentence are gone; the two real claims are not.
  assert.equal(result.claims.length, 2);
  assert.ok(result.claims.every((c) => !/subscribe/i.test(c.text)));
  assert.deepEqual(result.claims.map((c) => c.start), [5, 20]);

  // The egg claim matched a "Mostly True" review; the coffee claim matched nothing.
  assert.equal(result.claims[0].matches.length, 1);
  assert.equal(result.claims[0].matches[0].reviews[0].publisher, "FactCheck.example");
  assert.equal(result.claims[1].matches.length, 0);

  assert.equal(result.factCheck.matched, 1);
  assert.equal(result.factCheck.checked, 2);
  assert.equal(typeof result.score, "number");
  assert.ok(result.score > 0 && result.score <= 100);
  assert.equal(result.band, result.score >= 70 ? "green" : result.score >= 45 ? "yellow" : "red");

  // Page signals reached the scorer even with no YouTube Data API key.
  assert.equal(result.channelSignals.subscriberCount, 1200000);
  assert.equal(result.channelSignals.source, "watch-page");
  assert.ok(result.searchUrl.includes("fact%20check"));

  // Two lookups, one per claim, and no other network calls.
  assert.equal(calls.apiFetches.length, 2);
  assert.ok(calls.apiFetches.every((u) => u.includes("factchecktools")));
});

test("the second look at the same video is served from the cache", async () => {
  await reset();
  await send({ type: "wwi:analyze", videoId: VIDEO_ID, pageSignals: {} });
  const before = calls.apiFetches.length;

  const cached = await send({ type: "wwi:analyze", videoId: VIDEO_ID, pageSignals: {} });
  assert.equal(cached.fromCache, true);
  assert.equal(calls.apiFetches.length, before, "no lookups are repeated");

  const forced = await send({ type: "wwi:analyze", videoId: VIDEO_ID, pageSignals: {}, force: true });
  assert.notEqual(forced.fromCache, true);
  assert.ok(calls.apiFetches.length > before, "a forced re-check really re-checks");
});

test("the live player response is used when it matches, skipping the page fetch", async () => {
  await reset();
  config.livePlayer = true;

  const result = await send({ type: "wwi:analyze", videoId: VIDEO_ID, pageSignals: {} });
  assert.equal(result.status, "ok");
  assert.equal(calls.executeScript, 1);
  assert.ok(
    calls.tabFetches.every((url) => url.includes("timedtext")),
    "the watch page is not re-fetched when the player is already correct"
  );
});

test("a stale player response is ignored in favour of the served page", async () => {
  await reset();
  config.livePlayer = true;

  // The player still holds the previous video, which is what SPA navigation leaves behind.
  const result = await send({ type: "wwi:analyze", videoId: "zzz11111111", pageSignals: {} });
  assert.ok(
    calls.tabFetches.some((url) => url.includes("/watch?v=zzz11111111")),
    "the page is fetched when the live player response is for another video"
  );
  assert.equal(result.status, "ok");
});

test("a video with no captions stops gracefully and is remembered", async () => {
  await reset();
  config.serveCaptions = false;

  const result = await send({ type: "wwi:analyze", videoId: VIDEO_ID, pageSignals: {} });
  assert.equal(result.status, "no-transcript");
  assert.equal(result.transient, false, "an empty caption track is not a transient failure");
  assert.equal(result.score, null);
  assert.equal(result.claims.length, 0);
  assert.match(result.reason, /No captions are available/);
  assert.equal(calls.apiFetches.length, 0, "nothing is looked up when there is nothing to look up");

  const again = await send({ type: "wwi:analyze", videoId: VIDEO_ID, pageSignals: {} });
  assert.equal(again.fromCache, true);
});

test("without a fact-check key nothing is looked up, and the panel is told why", async () => {
  await reset({ factCheckApiKey: "" });

  const result = await send({ type: "wwi:analyze", videoId: VIDEO_ID, pageSignals: {} });
  assert.equal(result.unverified, true);
  assert.equal(result.score, null);
  assert.equal(result.claims.length, 2, "claims are still extracted and shown");
  assert.match(result.reason, /No Fact Check API key/);
  assert.equal(calls.apiFetches.length, 0);
  assert.ok(result.warnings.some((w) => /No Fact Check API key/.test(w)));
});

test("an unreadable page is reported as such and is not cached as 'no captions'", async () => {
  await reset();
  config.tabFails = true;

  const result = await send({ type: "wwi:analyze", videoId: VIDEO_ID, pageSignals: {} });
  assert.equal(result.status, "no-transcript");
  assert.equal(result.transient, true);
  assert.match(result.reason, /Could not read this page's caption list/);

  const stored = await storage.get(null);
  assert.ok(
    !Object.keys(stored).some((key) => key.includes(VIDEO_ID)),
    "a failure we might recover from is never written to the cache"
  );
});

test("clearing the cache actually clears it, and leaves the settings alone", async () => {
  await reset();
  await send({ type: "wwi:analyze", videoId: VIDEO_ID, pageSignals: {} });
  assert.ok(Object.keys(await storage.get(null)).some((k) => k.includes(VIDEO_ID)));

  await send({ type: "wwi:clear-cache" });
  const after = await storage.get(null);
  assert.ok(!Object.keys(after).some((k) => k.includes(VIDEO_ID)));
  assert.equal((await send({ type: "wwi:get-settings" })).factCheckApiKey, "fc-key");
});

test("the AI tier replaces extraction only - the lookup and score still run", async () => {
  await reset({ aiEnabled: true, aiProvider: "gemini", aiApiKey: "ai-key" });
  config.aiResponse = {
    claims: [
      {
        quote: "Egg prices rose 12 percent last year, according to the Department of Agriculture.",
        claim: "The USDA reported that egg prices rose 12% in the last year.",
        why_checkable: "Cited statistic",
        currency: "Prices move monthly; this figure is already a year old.",
        search_query: "usda egg prices 12 percent",
      },
    ],
    summary: "One checkable price claim, already stale.",
    caveats: "Auto-captions.",
  };

  const result = await send({ type: "wwi:analyze", videoId: VIDEO_ID, pageSignals: {} });

  assert.equal(result.tier, "ai");
  assert.equal(result.ai.summary, "One checkable price claim, already stale.");
  assert.equal(result.ai.model, "gemini-2.5-flash");
  assert.equal(result.claims.length, 1, "the model's claims replaced the heuristic ones");
  assert.equal(result.claims[0].text, "The USDA reported that egg prices rose 12% in the last year.");
  assert.equal(result.claims[0].start, 5, "the timestamp is recovered from the transcript");
  assert.equal(result.claims[0].currency, "Prices move monthly; this figure is already a year old.");

  // Still one model call, and the same fact-check lookup afterwards.
  assert.equal(calls.apiFetches.filter((u) => u.includes("generativelanguage")).length, 1);
  assert.equal(calls.apiFetches.filter((u) => u.includes("factchecktools")).length, 1);
  assert.equal(result.claims[0].matches.length, 1);
  assert.equal(typeof result.score, "number");
});

test("when the AI tier fails the free heuristics still produce a result", async () => {
  await reset({ aiEnabled: true, aiProvider: "gemini", aiApiKey: "ai-key" });
  config.aiFails = true;

  const result = await send({ type: "wwi:analyze", videoId: VIDEO_ID, pageSignals: {} });

  assert.equal(result.tier, "free");
  assert.equal(result.claims.length, 2, "the regex extraction took over");
  assert.equal(typeof result.score, "number");
  assert.ok(result.warnings.some((w) => /AI tier failed.*quota exhausted/.test(w)));
});

test("the AI tier is not even loaded unless it is switched on with a key", async () => {
  await reset({ aiEnabled: true, aiApiKey: "" });
  const result = await send({ type: "wwi:analyze", videoId: VIDEO_ID, pageSignals: {} });
  assert.equal(result.tier, "free");
  assert.equal(calls.apiFetches.filter((u) => u.includes("generativelanguage")).length, 0);
  assert.ok(result.warnings.some((w) => /no API key/i.test(w)));
});

test("unknown messages are refused rather than silently ignored", async () => {
  const result = await send({ type: "wwi:nonsense" });
  assert.equal(result.status, "error");
  assert.match(result.error, /unknown message/);
});
