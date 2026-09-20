import test from "node:test";
import assert from "node:assert/strict";

import { describeGoogleError, testFactCheckKey, testYouTubeKey } from "../lib/keytest.js";

const reply = (status, body) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => body,
});

test("a working key says so, and says what came back", async () => {
  const result = await testFactCheckKey("AIza-good", async (url) => {
    assert.ok(String(url).includes("factchecktools.googleapis.com"));
    assert.ok(String(url).includes("key=AIza-good"));
    return reply(200, { claims: [{ text: "x" }] });
  });
  assert.equal(result.ok, true);
  assert.match(result.detail, /Working/);
});

test("the common failure - a valid key on a project without the API - is named", async () => {
  const body = {
    error: {
      code: 403,
      status: "PERMISSION_DENIED",
      message:
        "Fact Check Tools API has not been used in project 12345 before or it is disabled. Enable it by visiting https://console.cloud.google.com/apis/api/factchecktools.googleapis.com/overview?project=12345 then retry.",
      details: [{ reason: "SERVICE_DISABLED" }],
    },
  };
  const result = await testFactCheckKey("AIza-valid", async () => reply(403, body));
  assert.equal(result.ok, false);
  assert.match(result.detail, /not enabled on its project/);
  assert.ok(result.fix.startsWith("https://console.cloud.google.com/"), "the console link is offered");
  assert.ok(!result.fix.endsWith(")"), "the url is not left with trailing punctuation");
});

test("an invalid key, a blocked key and an exhausted quota read differently", async () => {
  const invalid = await testFactCheckKey("nope", async () =>
    reply(400, { error: { message: "API key not valid. Please pass a valid API key.", details: [{ reason: "API_KEY_INVALID" }] } })
  );
  assert.match(invalid.detail, /not a valid API key/);

  const blocked = await testFactCheckKey("AIza-restricted", async () =>
    reply(403, { error: { message: "Requests from referer are blocked.", details: [{ reason: "API_KEY_HTTP_REFERRER_BLOCKED" }] } })
  );
  assert.match(blocked.detail, /application restrictions/);

  const exhausted = await testFactCheckKey("AIza-busy", async () =>
    reply(429, { error: { message: "Quota exceeded", status: "RESOURCE_EXHAUSTED" } })
  );
  assert.match(exhausted.detail, /quota is exhausted/);
});

test("an empty key never makes a request", async () => {
  let called = false;
  const result = await testFactCheckKey("", async () => ((called = true), reply(200, {})));
  assert.equal(called, false);
  assert.equal(result.ok, false);
  assert.match(result.detail, /No key/);
});

test("a network failure is reported as one, not as a bad key", async () => {
  const result = await testFactCheckKey("AIza-x", async () => {
    throw new Error("Failed to fetch");
  });
  assert.equal(result.ok, false);
  assert.match(result.detail, /Could not reach Google/);
});

test("the YouTube key is probed against the videos endpoint", async () => {
  const result = await testYouTubeKey("AIza-yt", async (url) => {
    assert.ok(String(url).includes("youtube/v3/videos"));
    return reply(200, { items: [{ id: "x" }] });
  });
  assert.equal(result.ok, true);
  assert.match(result.detail, /channel signals/);

  const empty = await testYouTubeKey("AIza-yt", async () => reply(200, { items: [] }));
  assert.equal(empty.ok, true, "an empty result set is still a working key");
});

test("an unrecognised error falls back to whatever Google said", () => {
  assert.equal(describeGoogleError(500, { error: { message: "Backend error" } }, "X").detail, "Backend error");
  assert.equal(describeGoogleError(418, null, "X").detail, "HTTP 418");
});
