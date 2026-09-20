import test from "node:test";
import assert from "node:assert/strict";

import {
  decodeEntities,
  joinCues,
  parseCaptions,
  parseJson3,
  parseTimedTextXml,
  pickTrack,
  timestampAt,
  withJson3,
} from "../lib/transcript.js";

test("json3 cues become text with timings", () => {
  const body = JSON.stringify({
    events: [
      { tStartMs: 0, dDurationMs: 1500, segs: [{ utf8: "hello " }, { utf8: "world" }] },
      { tStartMs: 1500, segs: [] },
      { tStartMs: 2000, dDurationMs: 1000, segs: [{ utf8: "again" }] },
    ],
  });
  const cues = parseJson3(body);
  assert.deepEqual(
    cues.map((c) => c.text),
    ["hello world", "again"]
  );
  assert.equal(cues[1].start, 2);
});

test("timedtext xml is parsed without a DOM", () => {
  const xml =
    '<?xml version="1.0"?><transcript>' +
    '<text start="4.5" dur="2.0">first &amp;amp; second</text>' +
    '<text start="7" dur="1">third<br/>line</text></transcript>';
  const cues = parseTimedTextXml(xml);
  assert.equal(cues.length, 2);
  assert.equal(cues[0].start, 4.5);
  assert.equal(cues[0].text, "first &amp; second");
  assert.equal(cues[1].text, "third line");
});

test("parseCaptions dispatches on the payload shape", () => {
  assert.equal(parseCaptions("").length, 0);
  assert.equal(parseCaptions('{"events":[{"tStartMs":0,"segs":[{"utf8":"hi"}]}]}')[0].text, "hi");
  assert.equal(parseCaptions('<text start="0">hi</text>')[0].text, "hi");
});

test("entities that actually turn up in captions are decoded", () => {
  assert.equal(decodeEntities("it&#39;s &quot;fine&quot; &amp; &lt;ok&gt;"), `it's "fine" & <ok>`);
});

test("a human english track beats the auto one, and any english beats none", () => {
  const tracks = [
    { languageCode: "es", kind: "", baseUrl: "es" },
    { languageCode: "en", kind: "asr", baseUrl: "en-asr" },
    { languageCode: "en", kind: "", baseUrl: "en-human" },
  ];
  assert.equal(pickTrack(tracks).baseUrl, "en-human");
  assert.equal(pickTrack([tracks[0], tracks[1]]).baseUrl, "en-asr");
  assert.equal(pickTrack([tracks[0]]).baseUrl, "es");
  assert.equal(pickTrack([]), null);
});

test("the rolling overlap in auto-captions is dropped, not repeated", () => {
  const cues = [
    { start: 0, text: "the price of eggs" },
    { start: 2, text: "the price of eggs went up by" },
    { start: 4, text: "went up by twelve percent" },
  ];
  const { text } = joinCues(cues);
  assert.equal(text, "the price of eggs went up by twelve percent");
});

test("character offsets map back to the moment they were said", () => {
  const { text, offsets } = joinCues([
    { start: 10, text: "alpha" },
    { start: 20, text: "bravo" },
    { start: 30, text: "charlie" },
  ]);
  assert.equal(text, "alpha bravo charlie");
  assert.equal(timestampAt(offsets, 0), 10);
  assert.equal(timestampAt(offsets, 7), 20);
  assert.equal(timestampAt(offsets, 15), 30);
});

test("json3 is requested without disturbing signed parameters", () => {
  assert.equal(withJson3("https://x/api/timedtext?v=1&sig=abc"), "https://x/api/timedtext?v=1&sig=abc&fmt=json3");
  assert.equal(withJson3("https://x/api/timedtext?fmt=srv3"), "https://x/api/timedtext?fmt=srv3");
});
