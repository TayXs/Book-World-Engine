import test from "node:test";
import assert from "node:assert/strict";

import {
  MAX_TRANSCRIPT_CHARS,
  PROVIDERS,
  buildPrompt,
  buildRequest,
  parseAiJson,
  parseResponse,
  runAiTier,
  toClaims,
} from "../lib/ai.js";
import { joinCues } from "../lib/transcript.js";
import { locateInTranscript } from "../lib/claims.js";

const CUES = [
  { start: 0, text: "so anyway the price of eggs went up by twelve percent last year" },
  { start: 30, text: "and a study from harvard said coffee lowers heart disease risk" },
];

test("each provider builds a request its own API would accept", () => {
  const gemini = buildRequest("gemini", { apiKey: "k", prompt: "p" });
  assert.match(gemini.url, /generativelanguage\.googleapis\.com\/v1beta\/models\/gemini-2\.5-flash:generateContent$/);
  assert.equal(gemini.init.headers["x-goog-api-key"], "k");
  assert.deepEqual(JSON.parse(gemini.init.body).tools, [{ google_search: {} }]);

  const anthropic = buildRequest("anthropic", { apiKey: "k", prompt: "p" });
  assert.equal(anthropic.url, "https://api.anthropic.com/v1/messages");
  assert.equal(anthropic.init.headers["anthropic-version"], "2023-06-01");
  assert.equal(anthropic.init.headers["anthropic-dangerous-direct-browser-access"], "true");
  const body = JSON.parse(anthropic.init.body);
  assert.equal(body.model, "claude-opus-5");
  assert.equal(body.tools[0].type, "web_search_20260209");
  assert.equal(body.tools[0].name, "web_search");
  assert.equal(body.output_config.effort, "medium");

  const openai = buildRequest("openai", { apiKey: "k", prompt: "p" });
  assert.equal(openai.url, "https://api.openai.com/v1/responses");
  assert.equal(openai.init.headers.Authorization, "Bearer k");
  assert.deepEqual(JSON.parse(openai.init.body).tools, [{ type: "web_search" }]);
});

test("a chosen model overrides the default, and search can be switched off", () => {
  const body = JSON.parse(buildRequest("anthropic", { apiKey: "k", prompt: "p", model: "claude-sonnet-5", webSearch: false }).init.body);
  assert.equal(body.model, "claude-sonnet-5");
  assert.equal(body.tools, undefined);
});

test("an unknown provider is refused rather than guessed at", () => {
  assert.throws(() => buildRequest("llama", { apiKey: "k", prompt: "p" }), /unknown provider/);
});

test("each provider's response shape yields its text", () => {
  assert.equal(parseResponse("gemini", { candidates: [{ content: { parts: [{ text: "a" }, { text: "b" }] } }] }), "ab");
  assert.equal(parseResponse("anthropic", { content: [{ type: "thinking" }, { type: "text", text: "hi" }] }), "hi");
  assert.equal(
    parseResponse("openai", { output: [{ type: "message", content: [{ type: "output_text", text: "hi" }] }] }),
    "hi"
  );
  assert.equal(parseResponse("openai", { output_text: "hi" }), "hi");
});

test("a refusal or a block is an error with a reason, not empty output", () => {
  assert.throws(
    () => parseResponse("anthropic", { stop_reason: "refusal", stop_details: { category: "cyber" } }),
    /declined.*cyber/
  );
  assert.throws(() => parseResponse("gemini", { promptFeedback: { blockReason: "SAFETY" } }), /blocked.*SAFETY/);
  assert.throws(() => parseResponse("gemini", { candidates: [{ finishReason: "MAX_TOKENS", content: {} }] }), /MAX_TOKENS/);
  assert.throws(() => parseResponse("openai", { output: [] }), /no text/);
});

test("JSON survives code fences and surrounding chatter", () => {
  assert.deepEqual(parseAiJson('```json\n{"claims":[]}\n```'), { claims: [] });
  assert.deepEqual(parseAiJson('Sure! Here you go:\n{"claims":[],"summary":"s"}\nHope that helps.'), {
    claims: [],
    summary: "s",
  });
  assert.equal(parseAiJson("not json at all"), null);
  assert.equal(parseAiJson(""), null);
});

test("model claims are timestamped from the transcript, not from the model", () => {
  const joined = joinCues(CUES);
  const claims = toClaims(
    {
      claims: [
        {
          quote: "a study from harvard said coffee lowers heart disease risk",
          claim: "A Harvard study found coffee lowers heart disease risk.",
          why_checkable: "Cited study",
          currency: "The study is old; newer trials qualify it.",
          search_query: "harvard coffee heart disease study",
        },
        {
          quote: "the price of eggs went up by twelve percent last year",
          claim: "Egg prices rose 12% last year.",
          why_checkable: "Statistic",
        },
      ],
    },
    joined
  );

  assert.deepEqual(claims.map((c) => c.start), [0, 30], "claims come back in transcript order");
  assert.equal(claims[0].text, "Egg prices rose 12% last year.");
  assert.ok(claims[0].located);
  assert.ok(claims[0].query.length > 0, "a missing search_query falls back to the free-tier query builder");
  assert.equal(claims[1].query, "harvard coffee heart disease study");
  assert.equal(claims[1].currency, "The study is old; newer trials qualify it.");
});

test("a claim the model invented is flagged rather than silently timestamped", () => {
  const joined = joinCues(CUES);
  const [claim] = toClaims({ claims: [{ quote: "mars colonies will open in 2031", claim: "Mars colonies open in 2031." }] }, joined);
  assert.equal(claim.located, false);
  assert.ok(claim.signals.includes("not found in transcript"));
  assert.equal(locateInTranscript("mars colonies will open in 2031", joined).index, -1);
});

test("claims are capped and junk entries dropped", () => {
  const joined = joinCues(CUES);
  const claims = toClaims({ claims: [{ claim: "one" }, { quote: "two" }, {}, { claim: "three" }] }, joined, 2);
  assert.equal(claims.length, 2);
});

test("the prompt carries the video, the rules and the transcript", () => {
  const prompt = buildPrompt({ title: "T", channelTitle: "C", transcript: "words here", maxClaims: 7 });
  assert.ok(prompt.includes("Video title: T"));
  assert.ok(prompt.includes("at most 7 factual claims"));
  assert.ok(prompt.includes("Use web search"));
  assert.ok(prompt.trimEnd().endsWith("words here"));
});

test("end to end against a stubbed provider", async () => {
  let seen = null;
  const fetchImpl = async (url, init) => {
    seen = { url, init };
    return {
      ok: true,
      json: async () => ({
        candidates: [
          {
            content: {
              parts: [
                {
                  text:
                    '```json\n{"claims":[{"quote":"the price of eggs went up by twelve percent last year",' +
                    '"claim":"Egg prices rose 12% last year.","why_checkable":"Statistic","currency":"Stale by now.",' +
                    '"search_query":"egg prices 12 percent"}],"summary":"One claim.","caveats":"Auto-captions."}\n```',
                },
              ],
            },
          },
        ],
      }),
    };
  };

  const result = await runAiTier({
    cues: CUES,
    title: "Eggs",
    channelTitle: "Food",
    settings: { aiProvider: "gemini", aiApiKey: "k", maxClaims: 5 },
    fetchImpl,
  });

  assert.equal(result.provider, "gemini");
  assert.equal(result.model, "gemini-2.5-flash");
  assert.equal(result.summary, "One claim.");
  assert.equal(result.caveats, "Auto-captions.");
  assert.equal(result.transcriptTrimmed, false);
  assert.equal(result.claims.length, 1);
  assert.equal(result.claims[0].start, 0);
  assert.ok(seen.init.body.includes("price of eggs"), "the transcript is what got sent");
});

test("a provider error surfaces the provider's own message", async () => {
  const fetchImpl = async () => ({ ok: false, status: 401, json: async () => ({ error: { message: "invalid key" } }) });
  await assert.rejects(
    runAiTier({ cues: CUES, settings: { aiProvider: "anthropic", aiApiKey: "bad" }, fetchImpl }),
    /Anthropic Claude: invalid key/
  );
});

test("no key means the tier refuses to run rather than calling anything", async () => {
  let called = false;
  await assert.rejects(
    runAiTier({ cues: CUES, settings: { aiProvider: "gemini" }, fetchImpl: async () => ((called = true), {}) }),
    /no API key/
  );
  assert.equal(called, false);
});

test("an over-long transcript is trimmed and says so, rather than silently", async () => {
  const long = [{ start: 0, text: "word ".repeat(MAX_TRANSCRIPT_CHARS / 2) }];
  const fetchImpl = async () => ({
    ok: true,
    json: async () => ({ candidates: [{ content: { parts: [{ text: '{"claims":[{"claim":"c","quote":"word word"}]}' }] } }] }),
  });
  const result = await runAiTier({ cues: long, settings: { aiProvider: "gemini", aiApiKey: "k" }, fetchImpl });
  assert.equal(result.transcriptTrimmed, true);
});

test("every provider is described well enough for the options page", () => {
  for (const [name, config] of Object.entries(PROVIDERS)) {
    assert.ok(config.label, name);
    assert.ok(config.defaultModel, name);
    assert.ok(config.keyUrl.startsWith("https://"), name);
    assert.ok(config.host.startsWith("https://"), name);
    assert.ok(config.note, name);
  }
});
