import test from "node:test";
import assert from "node:assert/strict";

import {
  ageInDays,
  band,
  channelComponent,
  confidenceScore,
  formatCount,
  parseCountText,
} from "../lib/score.js";

const NOW = Date.parse("2026-09-20T00:00:00Z");
const CHANNEL = {
  subscriberCount: 850000,
  channelPublishedAt: "2016-02-01T00:00:00Z",
  uploadsPerMonth: 4.2,
  publishedAt: "2026-08-25T00:00:00Z",
};

test("no fact-check match means no score, and a stated reason", () => {
  const result = confidenceScore({ factCheck: { checked: 8, matched: 0, meanPolarity: 0 }, channel: CHANNEL, now: NOW });
  assert.equal(result.score, null);
  assert.equal(result.unverified, true);
  assert.match(result.reason, /No published fact-check/);
  assert.ok(result.channel.parts.length > 0, "channel signals are still reported");
});

test("no claims at all is reported differently from no matches", () => {
  const result = confidenceScore({ factCheck: { checked: 0, matched: 0, meanPolarity: 0 }, channel: CHANNEL, now: NOW });
  assert.match(result.reason, /No checkable claims/);
});

test("supported claims score green, refuted claims score red", () => {
  const supported = confidenceScore({ factCheck: { checked: 8, matched: 4, meanPolarity: 0.85 }, channel: CHANNEL, now: NOW });
  const refuted = confidenceScore({ factCheck: { checked: 8, matched: 5, meanPolarity: -0.9 }, channel: CHANNEL, now: NOW });
  assert.equal(supported.band, "green");
  assert.equal(refuted.band, "red");
  assert.ok(supported.score > refuted.score + 40);
});

test("thin coverage is pulled back toward neutral rather than swinging the score", () => {
  const thin = confidenceScore({ factCheck: { checked: 10, matched: 1, meanPolarity: -1 }, channel: CHANNEL, now: NOW });
  const broad = confidenceScore({ factCheck: { checked: 10, matched: 6, meanPolarity: -1 }, channel: CHANNEL, now: NOW });
  assert.ok(thin.score > broad.score, "one lookup should not condemn a video");
  assert.equal(thin.factCheck.coverage, 1 / 3);
  assert.equal(broad.factCheck.coverage, 1);
});

test("a fresh video from an established channel beats a stale one from a new channel", () => {
  const fact = { checked: 5, matched: 2, meanPolarity: 0.5 };
  const fresh = confidenceScore({ factCheck: fact, channel: CHANNEL, now: NOW });
  const stale = confidenceScore({
    factCheck: fact,
    channel: { subscriberCount: 300, channelPublishedAt: "2026-06-01T00:00:00Z", uploadsPerMonth: 38, publishedAt: "2019-01-01T00:00:00Z" },
    now: NOW,
  });
  assert.ok(fresh.score > stale.score);
});

test("channel signals stay inside 0..1 and explain themselves", () => {
  const component = channelComponent(CHANNEL, NOW);
  assert.ok(component.value > 0 && component.value <= 1);
  assert.deepEqual(
    component.parts.map((p) => p.label),
    ["Channel reach", "Channel tenure", "Upload cadence", "Video recency"]
  );
  assert.ok(component.parts.every((p) => p.value >= 0 && p.value <= 1));
  assert.match(component.parts[0].detail, /850\.0K subscribers/);
  assert.equal(component.parts.reduce((sum, p) => sum + p.weight, 0), 1);
});

test("missing channel data lands mid-scale instead of punishing the video", () => {
  const unknown = channelComponent({}, NOW);
  assert.ok(unknown.value > 0.35 && unknown.value < 0.65);
  assert.match(unknown.parts[0].detail, /hidden/);
});

test("a firehose upload schedule scores below a steady one", () => {
  const steady = channelComponent({ ...CHANNEL, uploadsPerMonth: 6 }, NOW);
  const firehose = channelComponent({ ...CHANNEL, uploadsPerMonth: 45 }, NOW);
  assert.ok(steady.value > firehose.value);
});

test("bands are the documented cutoffs", () => {
  assert.equal(band(70), "green");
  assert.equal(band(69), "yellow");
  assert.equal(band(45), "yellow");
  assert.equal(band(44), "red");
  assert.equal(band(null), "unverified");
});

test("counts are read off the page and written back for humans", () => {
  assert.equal(parseCountText("1.2M subscribers"), 1200000);
  assert.equal(parseCountText("874 subscribers"), 874);
  assert.equal(parseCountText("2.4K views"), 2400);
  assert.equal(parseCountText(""), null);
  assert.equal(formatCount(1200000), "1.2M");
  assert.equal(formatCount(874), "874");
});

test("age in days copes with junk", () => {
  assert.equal(ageInDays(null), null);
  assert.equal(ageInDays("not a date"), null);
  assert.equal(Math.round(ageInDays("2026-09-10T00:00:00Z", NOW)), 10);
});
