import test from "node:test";
import assert from "node:assert/strict";

import { checkClaims, normalizeClaim, ratingPolarity, searchClaim, summarizeMatches } from "../lib/factcheck.js";

test("publisher ratings map onto a polarity, or onto nothing", () => {
  assert.equal(ratingPolarity("True"), 1);
  assert.equal(ratingPolarity("Mostly true"), 0.7);
  assert.equal(ratingPolarity("Half True"), 0);
  assert.equal(ratingPolarity("Misleading"), -0.5);
  assert.equal(ratingPolarity("Pants on Fire!"), -1);
  assert.equal(ratingPolarity("False"), -1);
  assert.equal(ratingPolarity("Research in progress"), null);
  assert.equal(ratingPolarity(""), null);
});

test("reviews without a url are dropped", () => {
  const claim = normalizeClaim({
    text: "x",
    claimReview: [{ url: "https://a/1", textualRating: "False", publisher: { name: "A" } }, { textualRating: "True" }],
  });
  assert.equal(claim.reviews.length, 1);
  assert.equal(claim.reviews[0].polarity, -1);
});

const response = (claims) => ({
  ok: true,
  status: 200,
  json: async () => ({ claims }),
});

test("a fact-check about a different claim is not evidence about this one", async () => {
  const fetchImpl = async () =>
    response([
      {
        text: "Norway banned petrol cars in 2019",
        claimReview: [{ url: "https://p/1", textualRating: "False", publisher: { name: "P" } }],
      },
    ]);
  const result = await searchClaim(
    { text: "Coffee lowers the risk of heart disease by 15 percent", query: "coffee heart disease 15 percent" },
    { apiKey: "k", fetchImpl }
  );
  assert.deepEqual(result.matches, []);
});

test("a matching fact-check comes back with its quality score", async () => {
  const fetchImpl = async () =>
    response([
      {
        text: "Electric vehicle sales doubled in Norway between 2020 and 2023",
        claimReview: [
          { url: "https://p/1", textualRating: "Mostly True", publisher: { name: "Politi" }, reviewDate: "2024-02-01" },
        ],
      },
    ]);
  const result = await searchClaim(
    { text: "Electric vehicle sales doubled in Norway between 2020 and 2023", query: "electric vehicle Norway 2020 2023" },
    { apiKey: "k", fetchImpl }
  );
  assert.equal(result.matches.length, 1);
  assert.equal(result.matches[0].quality, 1);
  assert.equal(result.matches[0].reviews[0].polarity, 0.7);
});

test("no key means no call, and says so", async () => {
  let called = false;
  const result = await searchClaim({ text: "x", query: "x" }, { fetchImpl: async () => ((called = true), response([])) });
  assert.equal(called, false);
  assert.equal(result.skipped, "no-key");
});

test("an http error is reported, not thrown", async () => {
  const result = await searchClaim(
    { text: "x", query: "x" },
    { apiKey: "bad", fetchImpl: async () => ({ ok: false, status: 403 }) }
  );
  assert.equal(result.error, "key rejected");
  assert.deepEqual(result.matches, []);
});

test("checkClaims keeps results aligned with the claims that produced them", async () => {
  const claims = [
    { text: "Coffee lowers heart disease risk", query: "coffee heart disease" },
    { text: "Norway doubled electric vehicle sales", query: "norway electric vehicle" },
    { text: "The drug trial enrolled 30000 people", query: "drug trial 30000" },
  ];
  // The stub echoes the claim back, so every claim matches its own lookup - the
  // point of the test is that the results stay in the caller's order.
  const fetchImpl = async (url) => {
    const query = new URL(url).searchParams.get("query");
    const claim = claims.find((c) => c.query === query);
    return response([{ text: claim.text, claimReview: [{ url: `https://p/${query}`, textualRating: "True" }] }]);
  };
  const results = await checkClaims(claims, { apiKey: "k", fetchImpl, concurrency: 2 });
  assert.deepEqual(
    results.map((r) => r.claim.query),
    ["coffee heart disease", "norway electric vehicle", "drug trial 30000"]
  );
  assert.deepEqual(
    results.map((r) => r.matches[0].reviews[0].url),
    ["https://p/coffee heart disease", "https://p/norway electric vehicle", "https://p/drug trial 30000"]
  );
});

test("the summary weights matched claims and ignores unrated ones", () => {
  const summary = summarizeMatches([
    { matches: [{ quality: 1, reviews: [{ polarity: 1 }, { polarity: 0.7 }] }] },
    { matches: [] },
    { matches: [{ quality: 0.5, reviews: [{ polarity: null }] }] },
  ]);
  assert.equal(summary.checked, 3);
  assert.equal(summary.matched, 1);
  assert.equal(summary.reviews, 2);
  assert.ok(Math.abs(summary.meanPolarity - 0.85) < 1e-9);
});
