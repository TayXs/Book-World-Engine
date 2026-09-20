import test from "node:test";
import assert from "node:assert/strict";

import {
  extractPlayerResponse,
  factCheckSearchUrl,
  normalizePageSignals,
  parseWatchDate,
  summarizePlayerResponse,
  videoIdFromUrl,
} from "../lib/ytpage.js";
import { parseCountText } from "../lib/score.js";
import { uploadsPerMonth, mergeSignals } from "../lib/channel.js";

const NOW = Date.parse("2026-09-20T12:00:00Z");

test("every YouTube url shape yields the same id", () => {
  for (const url of [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s",
    "https://youtu.be/dQw4w9WgXcQ",
    "https://www.youtube.com/shorts/dQw4w9WgXcQ",
    "https://www.youtube.com/embed/dQw4w9WgXcQ",
    "https://www.youtube.com/live/dQw4w9WgXcQ",
  ]) {
    assert.equal(videoIdFromUrl(url), "dQw4w9WgXcQ", url);
  }
  assert.equal(videoIdFromUrl("https://www.youtube.com/feed/subscriptions"), null);
  assert.equal(videoIdFromUrl(""), null);
});

test("the player response survives braces and quotes inside its own strings", () => {
  const html =
    '<script>var ytInitialPlayerResponse = {"videoDetails":{"videoId":"abc12345678",' +
    '"title":"Why } matters and \\"quotes\\" too","author":"Chan","lengthSeconds":"600"},' +
    '"captions":{"playerCaptionsTracklistRenderer":{"captionTracks":[' +
    '{"baseUrl":"https://y/timedtext?v=1","languageCode":"en","kind":"asr","name":{"simpleText":"English (auto)"}},' +
    '{"languageCode":"fr"}]}}};var other = 1;</script>';
  const summary = summarizePlayerResponse(extractPlayerResponse(html));
  assert.equal(summary.videoId, "abc12345678");
  assert.equal(summary.title, 'Why } matters and "quotes" too');
  assert.equal(summary.lengthSeconds, 600);
  assert.equal(summary.tracks.length, 1, "a track with no baseUrl is useless");
  assert.equal(summary.tracks[0].name, "English (auto)");
});

test("a page without a player response returns null rather than throwing", () => {
  assert.equal(extractPlayerResponse("<html>consent wall</html>"), null);
  assert.equal(extractPlayerResponse("ytInitialPlayerResponse = {broken"), null);
  assert.equal(summarizePlayerResponse(null), null);
});

test("the date line under a video is parsed in all its wordings", () => {
  assert.equal(parseWatchDate("3 weeks ago", NOW).slice(0, 10), "2026-08-30");
  assert.equal(parseWatchDate("Premiered Sep 12, 2026", NOW).slice(0, 10), "2026-09-12");
  assert.equal(parseWatchDate("Streamed live on Jan 4, 2024", NOW).slice(0, 10), "2024-01-04");
  assert.equal(parseWatchDate("1 year ago", NOW).slice(0, 4), "2025");
  assert.equal(parseWatchDate("gibberish", NOW), null);
  assert.equal(parseWatchDate("", NOW), null);
});

test("page signals become the fields the scorer expects", () => {
  const signals = normalizePageSignals(
    { title: "T", channelTitle: "C", subscriberText: "1.2M subscribers", viewText: "345K views", dateText: "2 months ago" },
    NOW,
    parseCountText
  );
  assert.equal(signals.subscriberCount, 1200000);
  assert.equal(signals.viewCount, 345000);
  assert.equal(signals.publishedAt.slice(0, 7), "2026-07");
});

test("API signals win where they exist, page signals fill the rest", () => {
  const merged = mergeSignals(
    { title: "page title", subscriberCount: 1200, channelTitle: "C" },
    { available: true, subscriberCount: 1234, publishedAt: "2026-01-01T00:00:00Z", channelTitle: "" }
  );
  assert.equal(merged.subscriberCount, 1234);
  assert.equal(merged.channelTitle, "C", "an empty API field does not erase a known one");
  assert.equal(merged.title, "page title");
  assert.equal(merged.source, "youtube-data-api");
  assert.equal(mergeSignals({}, { available: false }).source, "watch-page");
});

test("upload cadence is the gap between uploads, and needs at least two dates", () => {
  assert.equal(uploadsPerMonth([]), null);
  assert.equal(uploadsPerMonth(["2026-09-01"]), null);
  assert.equal(uploadsPerMonth(["2026-09-01", "2026-09-01"]), null, "a zero span is not a rate");

  // Thirteen weekly uploads span twelve gaps, so the rate is ~4.3 a month.
  const weekly = Array.from({ length: 13 }, (_, i) =>
    new Date(Date.parse("2026-09-01T00:00:00Z") - i * 7 * 86400000).toISOString()
  );
  assert.ok(Math.abs(uploadsPerMonth(weekly) - 4.34) < 0.05);

  // Monthly uploads: three dates, two gaps, one a month.
  assert.ok(Math.abs(uploadsPerMonth(["2026-09-01", "2026-08-01", "2026-07-02"]) - 1) < 0.05);
});

test("the manual next step is a real search url", () => {
  const url = factCheckSearchUrl("Is coffee good for you?", "Health Channel");
  assert.ok(url.startsWith("https://www.google.com/search?q="));
  assert.ok(decodeURIComponent(url).includes("fact check"));
});
