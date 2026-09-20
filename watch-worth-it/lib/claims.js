/**
 * Free-tier claim extraction: no model, no key, no call. Just the observation
 * that a sentence worth checking usually carries a number, an absolute, or a
 * borrowed authority - and that "smash that subscribe button" carries none.
 *
 * Pure functions only; the service worker and `node --test` both import this.
 */

import { joinCues, timestampAt } from "./transcript.js";

const NUMBER = /\b\d[\d,.]*\b/;
const QUANTITY =
  /\b\d[\d,.]*\s?(?:%|percent|percentage points?|million|billion|trillion|thousand|k|x|times|years?|months?|days?|hours?|minutes?|degrees?|pounds?|kilos?|kg|lbs?|miles?|km|dollars?|calories?|milligrams?|mg|grams?|g)\b/i;
const YEAR = /\b(?:1[89]|20)\d{2}\b/;
const MONEY = /[$€£¥]\s?\d|\b\d[\d,.]*\s?(?:dollars|euros|pounds)\b/i;

const SUPERLATIVES =
  /\b(?:first|best|worst|only|never|always|proven|guaranteed|cure[sd]?|fastest|safest|largest|biggest|smallest|strongest|healthiest|cheapest|most|least|number one|#1|every(?:one|body)|no ?body|unprecedented|revolutionary|breakthrough)\b/i;
const AUTHORITY =
  /\b(?:study|studies|research(?:ers)?|scientists?|data|survey|trial|meta-?analysis|according to|report(?:s|ed)?|evidence|statistics|experts?|doctors?|fda|cdc|who|nasa|nih|epa|un|world health organization|harvard|stanford|mit|peer[- ]reviewed|published|journal)\b/i;
const CHANGE =
  /\b(?:increas\w+|decreas\w+|doubl\w+|tripl\w+|halv\w+|rose|fell|dropp\w+|surg\w+|grew|shrank|more than|less than|fewer than|up from|down from|compared to|versus|vs\.?)\b/i;
const CAUSAL = /\b(?:causes?|caused|leads? to|results? in|prevents?|reduces?|eliminates?|linked to|responsible for)\b/i;

const HEDGES =
  /\b(?:i think|i believe|i feel|in my opinion|maybe|perhaps|probably|might be|could be|i guess|imagine if|what if|let's say|suppose)\b/i;
const BOILERPLATE =
  /\b(?:subscribe|smash that|like and share|link in the (?:description|bio)|comment below|patreon|sponsor(?:ed|ship)?|promo code|use code|check out my|merch|notification bell|thanks for watching|welcome back to)\b/i;
const FILLER = /^(?:so|and|but|okay|ok|right|now|well|um|uh|yeah|you know)\b/i;

const STOPWORDS = new Set(
  ("a about above after again against all am an and any are as at be because been before being below between both but by " +
    "can cannot could did do does doing down during each few for from further had has have having he her here hers him his " +
    "how i if in into is it its just like me more most my no nor not now of off on once only or other our out over own " +
    "really same she should so some such than that the their them then there these they this those through to too under " +
    "until up very was we were what when where which while who whom why will with would you your gonna going get got " +
    "actually basically literally know think see say said says thing things lot kind sort way").split(" ")
);

/** Sentence-per-line for punctuated captions; word windows for the ASR soup. */
export function splitUnits(text) {
  if (!text) return [];
  const punctuation = (text.match(/[.!?]/g) || []).length;
  const punctuated = punctuation > text.length / 400;

  const units = [];
  if (punctuated) {
    const pattern = /[^.!?]+[.!?]*/g;
    let match;
    while ((match = pattern.exec(text)) !== null) {
      const raw = match[0];
      const trimmed = raw.trim();
      if (trimmed) units.push({ text: trimmed, at: match.index + (raw.length - raw.trimStart().length) });
    }
    return units;
  }

  // No punctuation to lean on: cut ~28-word windows and let the scorer sort it out.
  const words = [];
  const pattern = /\S+/g;
  let match;
  while ((match = pattern.exec(text)) !== null) words.push({ word: match[0], at: match.index });
  for (let i = 0; i < words.length; i += 28) {
    const window = words.slice(i, i + 28);
    if (window.length < 6) break;
    units.push({ text: window.map((w) => w.word).join(" "), at: window[0].at });
  }
  return units;
}

/**
 * Why this sentence might be worth checking. Returns the reasons as well as the
 * number, because the panel shows the user what tripped the filter.
 */
export function scoreUnit(text) {
  const signals = [];
  let score = 0;
  const words = text.split(/\s+/).filter(Boolean);

  if (words.length < 6 || words.length > 60) return { score: 0, signals };
  if (/\?\s*$/.test(text)) return { score: 0, signals };
  if (BOILERPLATE.test(text)) return { score: 0, signals };

  if (QUANTITY.test(text)) {
    score += 3;
    signals.push("statistic");
  } else if (MONEY.test(text)) {
    score += 3;
    signals.push("money figure");
  } else if (YEAR.test(text)) {
    score += 2;
    signals.push("date");
  } else if (NUMBER.test(text)) {
    score += 1.5;
    signals.push("number");
  }

  if (AUTHORITY.test(text)) {
    score += 2.5;
    signals.push("cites authority");
  }
  if (SUPERLATIVES.test(text)) {
    score += 2;
    signals.push("absolute claim");
  }
  if (CHANGE.test(text)) {
    score += 1.5;
    signals.push("comparison");
  }
  if (CAUSAL.test(text)) {
    score += 1.5;
    signals.push("cause and effect");
  }

  // Proper nouns, ignoring the capital that merely starts the sentence.
  const proper = text.match(/(?:^|[^.!?]\s)([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)/g) || [];
  const named = proper.filter((p) => p.trim().length > 3).length;
  if (named >= 1) {
    score += Math.min(1.5, named * 0.5);
    signals.push("named entity");
  }

  if (HEDGES.test(text)) {
    score -= 2.5;
    signals.push("hedged");
  }
  if (FILLER.test(text)) score -= 0.25;

  return { score: Math.max(0, score), signals };
}

const normalize = (text) =>
  text
    .toLowerCase()
    .replace(/[^a-z0-9%$ ]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();

/**
 * Crude singularization. "egg prices" and "the price of eggs" are the same
 * claim, and a fact-check that says one should match a video that says the
 * other.
 */
function stem(word) {
  if (word.length > 3 && word.endsWith("ies")) return `${word.slice(0, -3)}y`;
  if (word.length > 3 && word.endsWith("s") && !word.endsWith("ss")) return word.slice(0, -1);
  return word;
}

/** Shared-word overlap, used both to dedupe claims and to grade fact-check hits. */
export function similarity(a, b) {
  // Numbers survive the length filter: "12" is the most distinguishing token in
  // "12 percent", and dropping it makes every percentage claim look alike.
  const tokens = (value) =>
    new Set(
      normalize(value)
        .split(" ")
        .filter((w) => (/\d/.test(w) ? w.length > 0 : w.length > 2) && !STOPWORDS.has(w))
        .map(stem)
    );
  const left = tokens(a);
  const right = tokens(b);
  if (left.size === 0 || right.size === 0) return 0;
  let shared = 0;
  for (const token of left) if (right.has(token)) shared += 1;
  return shared / Math.min(left.size, right.size);
}

/** The search string we hand to the fact-check index: content words and numbers. */
export function claimQuery(text, maxTerms = 8) {
  const terms = [];
  for (const raw of text.split(/\s+/)) {
    const word = raw.replace(/^[^A-Za-z0-9$€£%]+|[^A-Za-z0-9%]+$/g, "");
    if (!word) continue;
    const lower = word.toLowerCase();
    if (STOPWORDS.has(lower) || lower.length < 3) {
      if (!/\d/.test(word)) continue;
    }
    if (terms.some((t) => t.toLowerCase() === lower)) continue;
    terms.push(word);
    if (terms.length >= maxTerms) break;
  }
  return terms.join(" ");
}

/**
 * Transcript cues in, ranked candidate claims out.
 *
 * `minScore` is deliberately low: the fact-check lookup is free and a claim with
 * no match costs nothing but a row in the panel.
 */
export function extractClaims(cues, { max = 10, minScore = 3 } = {}) {
  const joined = Array.isArray(cues) ? joinCues(cues) : { text: String(cues || ""), offsets: [] };
  const units = splitUnits(joined.text);

  const scored = [];
  for (const unit of units) {
    const { score, signals } = scoreUnit(unit.text);
    if (score < minScore) continue;
    scored.push({
      text: unit.text.replace(/\s+/g, " ").trim(),
      score: Number(score.toFixed(2)),
      signals,
      start: timestampAt(joined.offsets, unit.at),
    });
  }

  scored.sort((a, b) => b.score - a.score || a.start - b.start);

  const kept = [];
  for (const candidate of scored) {
    if (kept.some((k) => similarity(k.text, candidate.text) > 0.7)) continue;
    kept.push({ ...candidate, query: claimQuery(candidate.text) });
    if (kept.length >= max) break;
  }

  kept.sort((a, b) => a.start - b.start);
  return kept;
}

export { STOPWORDS };

/**
 * Find where a quoted claim was actually said.
 *
 * The AI tier returns claim text but cannot be trusted with timestamps, so the
 * quote is located back in the transcript instead: exact match first, then
 * progressively shorter word shingles, since a model tends to tidy punctuation
 * and filler out of what it quotes.
 */
export function locateInTranscript(claimText, joined) {
  const haystack = (joined?.text || "").toLowerCase();
  const offsets = joined?.offsets || [];
  const needle = String(claimText || "").toLowerCase().replace(/\s+/g, " ").trim();
  if (!haystack || !needle) return { index: -1, start: 0 };

  const at = (index) => ({ index, start: timestampAt(offsets, index) });

  const exact = haystack.indexOf(needle);
  if (exact >= 0) return at(exact);

  const words = needle.replace(/[^a-z0-9% ]+/g, " ").split(/\s+/).filter(Boolean);
  for (const size of [8, 5, 3]) {
    if (words.length < size) continue;
    for (let i = 0; i + size <= words.length; i++) {
      const shingle = words.slice(i, i + size).join(" ");
      const found = haystack.indexOf(shingle);
      if (found >= 0) return at(found);
    }
  }
  return { index: -1, start: 0 };
}
