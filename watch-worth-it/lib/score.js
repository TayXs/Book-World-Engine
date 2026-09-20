/**
 * The 0-100 number, and the arithmetic behind it in plain sight.
 *
 * It is a weighted rule, not a model and not a truth claim. It answers one
 * narrow question: given the claims we could pull out of this transcript, how
 * much of what can be checked checks out - and does the channel behave like a
 * source that stands behind its numbers?
 */

const clamp = (value, low = 0, high = 1) => Math.min(high, Math.max(low, value));

export const WEIGHTS = { factCheck: 0.6, channel: 0.4 };

/** Channel and recency signals, each 0..1, each with a stated reason. */
export function channelComponent(signals = {}, now = Date.now()) {
  const parts = [];

  const subscribers = Number(signals.subscriberCount) || 0;
  // log scale: 1k subs ~ 0.43, 100k ~ 0.71, 10M ~ 1.0. Reach is weak evidence,
  // which is why it carries the smallest share.
  const reach = subscribers > 0 ? clamp(Math.log10(subscribers + 1) / 7) : 0.35;
  parts.push({
    label: "Channel reach",
    value: reach,
    weight: 0.25,
    detail: subscribers > 0 ? `${formatCount(subscribers)} subscribers` : "subscriber count hidden",
  });

  const channelAgeDays = ageInDays(signals.channelPublishedAt, now);
  const tenure = channelAgeDays === null ? 0.5 : clamp(channelAgeDays / (5 * 365));
  parts.push({
    label: "Channel tenure",
    value: tenure,
    weight: 0.2,
    detail: channelAgeDays === null ? "unknown" : `${Math.round(channelAgeDays / 365.25 * 10) / 10} years old`,
  });

  // A channel that never posts and a channel posting 40 times a month are both
  // harder to trust than one with a steady beat.
  const perMonth = Number(signals.uploadsPerMonth);
  let cadence = 0.5;
  let cadenceDetail = "unknown";
  if (Number.isFinite(perMonth) && perMonth > 0) {
    cadence = perMonth <= 12 ? clamp(0.4 + perMonth * 0.05) : clamp(1 - (perMonth - 12) / 40);
    cadenceDetail = `${perMonth.toFixed(1)} uploads/month`;
  }
  parts.push({ label: "Upload cadence", value: cadence, weight: 0.15, detail: cadenceDetail });

  const videoAgeDays = ageInDays(signals.publishedAt, now);
  let recency = 0.5;
  let recencyDetail = "unknown age";
  if (videoAgeDays !== null) {
    recency = videoAgeDays <= 30 ? 1 : clamp(1 - (videoAgeDays - 30) / (4 * 365), 0.35, 1);
    recencyDetail = describeAge(videoAgeDays);
  }
  parts.push({ label: "Video recency", value: recency, weight: 0.4, detail: recencyDetail });

  const total = parts.reduce((sum, p) => sum + p.value * p.weight, 0);
  return { value: clamp(total), parts };
}

/**
 * Combine. Coverage matters: two matched claims out of ten is thin evidence, so
 * the fact-check component is pulled back toward neutral rather than allowed to
 * swing the whole score on one lookup.
 */
export function confidenceScore({ factCheck, channel, now = Date.now() } = {}) {
  const channelPart = channelComponent(channel, now);
  const summary = factCheck || { checked: 0, matched: 0, meanPolarity: 0 };

  if (!summary.matched) {
    return {
      score: null,
      unverified: true,
      reason: unverifiedReason(summary),
      channel: channelPart,
      factCheck: null,
    };
  }

  const coverage = clamp(summary.matched / 3);
  const raw = 0.5 + 0.5 * clamp(summary.meanPolarity, -1, 1);
  const factValue = 0.5 + (raw - 0.5) * coverage;

  const score = Math.round(100 * (factValue * WEIGHTS.factCheck + channelPart.value * WEIGHTS.channel));

  return {
    score,
    unverified: false,
    band: band(score),
    channel: channelPart,
    factCheck: {
      value: factValue,
      coverage,
      matched: summary.matched,
      checked: summary.checked,
      meanPolarity: summary.meanPolarity,
      detail: `${summary.matched} of ${summary.checked} claims matched a published fact-check`,
    },
  };
}

/**
 * Why there is no score. "Nobody has checked this" and "we never looked" are
 * different statements, and the panel should not make the first one when the
 * second is true.
 */
function unverifiedReason(summary) {
  if (!summary.checked) return "No checkable claims found in the transcript.";
  if (summary.skipped >= summary.checked) {
    return "No Fact Check API key is set, so none of these claims were looked up.";
  }
  return "No published fact-check covers any of the claims in this video.";
}

/** red below 45, yellow to 69, green from 70. */
export function band(score) {
  if (score === null || score === undefined) return "unverified";
  if (score >= 70) return "green";
  if (score >= 45) return "yellow";
  return "red";
}

export function ageInDays(isoDate, now = Date.now()) {
  if (!isoDate) return null;
  const then = Date.parse(isoDate);
  if (Number.isNaN(then)) return null;
  return Math.max(0, (now - then) / 86400000);
}

export function describeAge(days) {
  if (days < 1) return "today";
  if (days < 45) return `${Math.round(days)} days old`;
  if (days < 730) return `${Math.round(days / 30.4)} months old`;
  return `${(days / 365.25).toFixed(1)} years old`;
}

export function formatCount(value) {
  const n = Number(value) || 0;
  if (n >= 1e9) return `${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return String(n);
}

/** "1.2M subscribers" off the page, when no API key is configured. */
export function parseCountText(text) {
  if (!text) return null;
  const match = /([\d.,]+)\s*([KMB])?/i.exec(String(text).replace(/\s+/g, " "));
  if (!match) return null;
  const base = Number(match[1].replace(/,/g, ""));
  if (!Number.isFinite(base)) return null;
  const suffix = (match[2] || "").toUpperCase();
  const multiplier = suffix === "B" ? 1e9 : suffix === "M" ? 1e6 : suffix === "K" ? 1e3 : 1;
  return Math.round(base * multiplier);
}
