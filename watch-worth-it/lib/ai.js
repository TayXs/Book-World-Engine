/**
 * The optional "AI upgrade" tier.
 *
 * It replaces one step - claim extraction - with a single model call that also
 * reasons about whether a claim is still current, using the provider's own
 * built-in web search where there is one. Everything downstream is unchanged:
 * the claims it returns still go through the same fact-check lookup and the
 * same scoring rule.
 *
 * This module is imported dynamically and only when the toggle is on, so the
 * free tier never loads it. The key is the user's own, stored locally, and
 * spent one call per video.
 */

import { claimQuery, locateInTranscript } from "./claims.js";
import { joinCues } from "./transcript.js";

export const MAX_TRANSCRIPT_CHARS = 48000;

export const PROVIDERS = {
  gemini: {
    label: "Google Gemini",
    defaultModel: "gemini-2.5-flash",
    keyUrl: "https://aistudio.google.com/apikey",
    host: "https://generativelanguage.googleapis.com/*",
    webSearch: true,
    note: "Free tier available with the same Google account you signed in with.",
  },
  anthropic: {
    label: "Anthropic Claude",
    defaultModel: "claude-opus-5",
    keyUrl: "https://console.anthropic.com/settings/keys",
    host: "https://api.anthropic.com/*",
    webSearch: true,
    note: "Paid API key. One call per video.",
  },
  openai: {
    label: "OpenAI",
    defaultModel: "gpt-5",
    keyUrl: "https://platform.openai.com/api-keys",
    host: "https://api.openai.com/*",
    webSearch: true,
    note: "Paid API key. One call per video.",
  },
};

/* ------------------------------------------------------------------- prompt */

export function buildPrompt({ title, channelTitle, transcript, maxClaims = 10, webSearch = true }) {
  return `You are preparing a pre-watch research brief for someone deciding whether this YouTube video is worth their time.

Video title: ${title || "(unknown)"}
Channel: ${channelTitle || "(unknown)"}
Today's date: ${new Date().toISOString().slice(0, 10)}

From the transcript below, pull out at most ${maxClaims} factual claims - statements presented as fact that could be checked against outside evidence. Ignore opinions, predictions, jokes, hypotheticals and channel boilerplate (sponsorships, subscribe prompts, merch).

For each claim:
- "quote": the claim as it was actually said, copied from the transcript as closely as you can. It is matched back against the transcript by string search, so do not paraphrase it.
- "claim": the same claim rewritten to stand on its own, with the speaker and subject made explicit ("he said it doubled" becomes "Ford said EV sales doubled in 2024").
- "why_checkable": one short phrase naming what makes it checkable (a statistic, a cited study, an absolute, a date).
- "currency": whether the claim depends on numbers or circumstances that go stale, and whether it still holds today.${
    webSearch ? " Use web search where it would change your answer." : ""
  }
- "search_query": a short query someone would use to verify it.

Then write:
- "summary": three sentences at most, on what this video is asserting and where its weak points are.
- "caveats": anything about the transcript itself that limits the above (missing context, auto-caption garbling, heavy editing).

Return JSON only, no prose and no code fences:
{"claims":[{"quote":"","claim":"","why_checkable":"","currency":"","search_query":""}],"summary":"","caveats":""}

TRANSCRIPT:
${transcript}`;
}

/* ---------------------------------------------------------------- providers */

/** Pure: everything needed to make the call, and nothing that makes it. */
export function buildRequest(provider, { model, apiKey, prompt, webSearch = true }) {
  const config = PROVIDERS[provider];
  if (!config) throw new Error(`unknown provider: ${provider}`);
  const chosen = model || config.defaultModel;
  const useSearch = webSearch && config.webSearch;

  if (provider === "gemini") {
    return {
      url: `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(chosen)}:generateContent`,
      init: {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-goog-api-key": apiKey },
        body: JSON.stringify({
          contents: [{ role: "user", parts: [{ text: prompt }] }],
          generationConfig: { temperature: 0.2 },
          ...(useSearch ? { tools: [{ google_search: {} }] } : {}),
        }),
      },
    };
  }

  if (provider === "anthropic") {
    return {
      url: "https://api.anthropic.com/v1/messages",
      init: {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": apiKey,
          "anthropic-version": "2023-06-01",
          // Required for a browser-origin request; without it the API refuses.
          "anthropic-dangerous-direct-browser-access": "true",
        },
        body: JSON.stringify({
          model: chosen,
          max_tokens: 16000,
          // Bulk extraction over a long transcript: medium is the cost-saving
          // step-down that still reasons about currency properly.
          output_config: { effort: "medium" },
          messages: [{ role: "user", content: prompt }],
          ...(useSearch
            ? { tools: [{ type: "web_search_20260209", name: "web_search", max_uses: 5 }] }
            : {}),
        }),
      },
    };
  }

  return {
    url: "https://api.openai.com/v1/responses",
    init: {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify({
        model: chosen,
        input: prompt,
        ...(useSearch ? { tools: [{ type: "web_search" }] } : {}),
      }),
    },
  };
}

/** Pure: the model's text, or a thrown error explaining why there is none. */
export function parseResponse(provider, payload) {
  if (provider === "gemini") {
    const blocked = payload?.promptFeedback?.blockReason;
    if (blocked) throw new Error(`Gemini blocked the request (${blocked}).`);
    const candidate = payload?.candidates?.[0];
    const text = (candidate?.content?.parts || [])
      .map((part) => part?.text || "")
      .join("")
      .trim();
    if (!text) throw new Error(`Gemini returned no text (${candidate?.finishReason || "unknown reason"}).`);
    return text;
  }

  if (provider === "anthropic") {
    if (payload?.stop_reason === "refusal") {
      throw new Error(`Claude declined this request (${payload?.stop_details?.category || "refusal"}).`);
    }
    const text = (payload?.content || [])
      .filter((block) => block?.type === "text")
      .map((block) => block.text)
      .join("")
      .trim();
    if (!text) throw new Error("Claude returned no text.");
    return text;
  }

  const output = payload?.output;
  if (typeof payload?.output_text === "string" && payload.output_text.trim()) return payload.output_text.trim();
  const text = (Array.isArray(output) ? output : [])
    .filter((item) => item?.type === "message")
    .flatMap((item) => item.content || [])
    .filter((block) => block?.type === "output_text")
    .map((block) => block.text)
    .join("")
    .trim();
  if (!text) throw new Error("OpenAI returned no text.");
  return text;
}

/** Models wrap JSON in fences and apologies however firmly you ask them not to. */
export function parseAiJson(text) {
  if (!text) return null;
  const withoutFences = String(text).replace(/```(?:json)?\s*([\s\S]*?)```/g, "$1").trim();
  const candidates = [withoutFences];
  const first = withoutFences.indexOf("{");
  const last = withoutFences.lastIndexOf("}");
  if (first >= 0 && last > first) candidates.push(withoutFences.slice(first, last + 1));

  for (const candidate of candidates) {
    try {
      const parsed = JSON.parse(candidate);
      if (parsed && typeof parsed === "object") return parsed;
    } catch {
      // try the next shape
    }
  }
  return null;
}

/**
 * Model output into the same claim shape the free tier produces, with the
 * timestamp recovered from the transcript rather than taken on trust.
 */
export function toClaims(parsed, joined, maxClaims = 10) {
  const raw = Array.isArray(parsed?.claims) ? parsed.claims : [];
  const claims = [];

  for (const item of raw) {
    const statement = String(item?.claim || item?.quote || "").trim();
    if (!statement) continue;
    const quote = String(item?.quote || statement).trim();
    const located = locateInTranscript(quote, joined);

    const signals = [];
    if (item?.why_checkable) signals.push(String(item.why_checkable).toLowerCase().slice(0, 40));
    if (located.index < 0) signals.push("not found in transcript");

    claims.push({
      text: statement,
      quote,
      start: located.start,
      located: located.index >= 0,
      signals,
      currency: String(item?.currency || "").trim(),
      query: String(item?.search_query || "").trim() || claimQuery(statement),
      score: null,
    });
    if (claims.length >= maxClaims) break;
  }

  claims.sort((a, b) => a.start - b.start);
  return claims;
}

/* -------------------------------------------------------------------- runner */

export async function runAiTier(
  { cues, title, channelTitle, settings, fetchImpl = fetch } = {}
) {
  const provider = settings?.aiProvider || "gemini";
  const config = PROVIDERS[provider];
  if (!config) throw new Error(`unknown provider: ${provider}`);
  if (!settings?.aiApiKey) throw new Error("no API key for the AI tier");

  const joined = joinCues(cues || []);
  const trimmed = joined.text.length > MAX_TRANSCRIPT_CHARS;
  const transcript = trimmed ? joined.text.slice(0, MAX_TRANSCRIPT_CHARS) : joined.text;

  const prompt = buildPrompt({
    title,
    channelTitle,
    transcript,
    maxClaims: settings.maxClaims || 10,
    webSearch: config.webSearch,
  });

  const { url, init } = buildRequest(provider, {
    model: settings.aiModel,
    apiKey: settings.aiApiKey,
    prompt,
  });

  const response = await fetchImpl(url, init);
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body?.error?.message || body?.error?.type || detail;
    } catch {
      // the status alone will have to do
    }
    throw new Error(`${config.label}: ${detail}`);
  }

  const parsed = parseAiJson(parseResponse(provider, await response.json()));
  if (!parsed) throw new Error(`${config.label} did not return usable JSON.`);

  const claims = toClaims(parsed, joined, settings.maxClaims || 10);
  if (claims.length === 0) throw new Error(`${config.label} found no checkable claims.`);

  return {
    claims,
    summary: String(parsed.summary || "").trim(),
    caveats: String(parsed.caveats || "").trim(),
    provider,
    model: settings.aiModel || config.defaultModel,
    transcriptTrimmed: trimmed,
  };
}
