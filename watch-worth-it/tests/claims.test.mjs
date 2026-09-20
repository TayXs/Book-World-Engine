import test from "node:test";
import assert from "node:assert/strict";

import { claimQuery, extractClaims, scoreUnit, similarity, splitUnits } from "../lib/claims.js";

test("channel boilerplate never becomes a claim", () => {
  for (const line of [
    "Welcome back to the channel, smash that subscribe button.",
    "Link in the description and use code SAVE20 for 20 percent off.",
    "Thanks for watching, see you next week.",
  ]) {
    assert.equal(scoreUnit(line).score, 0, line);
  }
});

test("opinions are hedged down, statistics are scored up", () => {
  const opinion = scoreUnit("I think this is probably the best phone ever made in my opinion.");
  const statistic = scoreUnit("A 2019 study found a 15 percent drop in emissions across the fleet.");
  assert.ok(statistic.score > opinion.score);
  assert.ok(statistic.signals.includes("statistic"));
  assert.ok(statistic.signals.includes("cites authority"));
  assert.ok(opinion.signals.includes("hedged"));
});

test("questions and fragments are not claims", () => {
  assert.equal(scoreUnit("So what does the data actually say about 40 percent of people?").score, 0);
  assert.equal(scoreUnit("Ten percent.").score, 0);
});

test("unpunctuated auto-captions still get split into units", () => {
  const words = Array.from({ length: 70 }, (_, i) => `word${i}`).join(" ");
  const units = splitUnits(words);
  assert.ok(units.length >= 2);
  assert.ok(units.every((u) => u.text.split(" ").length <= 28));
  assert.equal(units[0].at, 0);
});

test("punctuated transcripts split on sentence boundaries", () => {
  const units = splitUnits("First sentence here. Second one follows! Third?");
  assert.deepEqual(
    units.map((u) => u.text),
    ["First sentence here.", "Second one follows!", "Third?"]
  );
});

test("claims come back ranked, deduped, timestamped and query-ready", () => {
  const cues = [
    { start: 0, text: "Hey everyone, welcome back, please subscribe to the channel." },
    { start: 8, text: "Electric vehicle sales doubled in Norway between 2020 and 2023, according to government data." },
    { start: 20, text: "EV sales doubled in Norway between 2020 and 2023 according to the government." },
    { start: 40, text: "I reckon it might be quite good, maybe." },
    { start: 55, text: "The FDA approved the drug in 2021 after a trial of 30,000 people." },
  ];
  const claims = extractClaims(cues, { max: 5 });

  assert.equal(claims.length, 2, "the near-duplicate is collapsed and the filler dropped");
  assert.deepEqual(
    claims.map((c) => c.start),
    [8, 55],
    "claims are returned in transcript order"
  );
  assert.ok(claims[0].query.includes("Norway"));
  assert.ok(!claims[0].query.split(" ").includes("the"));
});

test("similarity ignores stopwords and is symmetric enough to dedupe", () => {
  assert.ok(similarity("the price of eggs rose by 12 percent", "egg prices rose 12 percent") > 0.5);
  assert.ok(similarity("the moon landing was in 1969", "coffee lowers heart disease risk") < 0.2);
});

test("the query keeps numbers even when they are short tokens", () => {
  assert.ok(claimQuery("it fell by 12 percent in 2023").includes("12"));
});
