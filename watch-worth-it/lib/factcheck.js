/**
 * Google's Fact Check Tools API: free, key-only, no billing account.
 *
 * It indexes what ClaimReview publishers (PolitiFact, Snopes, Full Fact, AFP,
 * and a few hundred others) have already written. It is a lookup, not a verdict
 * engine - most claims in most videos are simply not in it, and saying so
 * plainly is the honest outcome.
 */

import { similarity } from "./claims.js";

const ENDPOINT = "https://factchecktools.googleapis.com/v1alpha1/claims:search";

/**
 * Map a publisher's free-text rating onto -1 (refuted) .. +1 (supported).
 * Returns null when the wording means nothing we can score.
 */
export function ratingPolarity(rating) {
  if (!rating) return null;
  const text = String(rating).toLowerCase().trim();

  if (/\b(?:pants on fire|fabricat|hoax|fake|no evidence|baseless|debunk|incorrect|inaccurate)\b/.test(text)) return -1;
  if (/\bmostly false|largely false|mostly untrue\b/.test(text)) return -0.7;
  if (/\bhalf[- ]true|partly|partially|mixture|mixed|half right\b/.test(text)) return 0;
  if (/\bmisleading|missing context|exaggerat|out of context|overstat|cherry|unsupported|unproven\b/.test(text)) return -0.5;
  if (/\bmostly true|largely true|mostly accurate\b/.test(text)) return 0.7;
  if (/\b(?:true|correct|accurate|confirmed|verified|legit)\b/.test(text)) return 1;
  if (/\bfalse|untrue|wrong|myth|scam\b/.test(text)) return -1;
  if (/\bunverified|unclear|not enough|undetermined|research in progress\b/.test(text)) return null;
  return null;
}

/** Flatten one API claim into the reviews we can actually use. */
export function normalizeClaim(apiClaim) {
  const reviews = Array.isArray(apiClaim?.claimReview) ? apiClaim.claimReview : [];
  return {
    text: apiClaim?.text || "",
    claimant: apiClaim?.claimant || "",
    claimDate: apiClaim?.claimDate || "",
    reviews: reviews
      .map((review) => ({
        publisher: review?.publisher?.name || review?.publisher?.site || "unknown publisher",
        url: review?.url || "",
        title: review?.title || "",
        rating: review?.textualRating || "",
        reviewDate: review?.reviewDate || "",
        polarity: ratingPolarity(review?.textualRating),
      }))
      .filter((review) => review.url),
  };
}

/**
 * One claim, one query. `minSimilarity` guards against the API's habit of
 * returning a loosely related fact-check for any query with a famous noun in it:
 * a review of a different claim is not evidence about this one.
 */
export async function searchClaim(claim, { apiKey, minSimilarity = 0.45, pageSize = 5, fetchImpl = fetch } = {}) {
  if (!apiKey) return { claim, matches: [], skipped: "no-key" };
  const query = claim.query || claim.text;
  if (!query) return { claim, matches: [] };

  const url = `${ENDPOINT}?${new URLSearchParams({
    query,
    key: apiKey,
    languageCode: "en",
    pageSize: String(pageSize),
  })}`;

  let payload;
  try {
    const response = await fetchImpl(url, { method: "GET" });
    if (!response.ok) {
      const detail = response.status === 403 ? "key rejected" : `HTTP ${response.status}`;
      return { claim, matches: [], error: detail };
    }
    payload = await response.json();
  } catch (error) {
    return { claim, matches: [], error: String(error?.message || error) };
  }

  const matches = [];
  for (const apiClaim of payload?.claims || []) {
    const normalized = normalizeClaim(apiClaim);
    if (normalized.reviews.length === 0) continue;
    const quality = similarity(claim.text, normalized.text);
    if (quality < minSimilarity) continue;
    matches.push({ ...normalized, quality: Number(quality.toFixed(2)) });
  }

  matches.sort((a, b) => b.quality - a.quality);
  return { claim, matches: matches.slice(0, 3) };
}

/**
 * Every claim, in a small burst. Fact Check Tools is generous but not infinite,
 * and a video should never cost more than a dozen requests.
 */
export async function checkClaims(claims, options = {}) {
  const { concurrency = 4 } = options;
  const results = new Array(claims.length);
  let cursor = 0;

  const worker = async () => {
    while (cursor < claims.length) {
      const index = cursor++;
      results[index] = await searchClaim(claims[index], options);
    }
  };

  await Promise.all(Array.from({ length: Math.min(concurrency, claims.length) }, worker));
  return results;
}

/** The single number the score needs: how the matched reviews lean, on balance. */
export function summarizeMatches(results) {
  let weight = 0;
  let weighted = 0;
  let matched = 0;
  let reviews = 0;

  for (const result of results || []) {
    const rated = (result.matches || []).filter((m) => m.reviews.some((r) => r.polarity !== null));
    if (rated.length === 0) continue;
    matched += 1;
    const best = rated[0];
    const polarities = best.reviews.map((r) => r.polarity).filter((p) => p !== null);
    reviews += polarities.length;
    const mean = polarities.reduce((sum, p) => sum + p, 0) / polarities.length;
    weighted += mean * best.quality;
    weight += best.quality;
  }

  return {
    checked: (results || []).length,
    matched,
    reviews,
    meanPolarity: weight > 0 ? weighted / weight : 0,
  };
}

export { ENDPOINT };
