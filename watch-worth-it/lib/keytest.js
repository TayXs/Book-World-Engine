/**
 * "Is this key any good?" - answered against the live API, in one call, with an
 * error message that names the actual problem.
 *
 * A key that is merely valid is not enough: the common failure is a real key
 * whose project never had the API enabled, and a bare "403" sends people back
 * to the console with nothing to look for.
 */

/** Turn Google's error envelope into something worth reading. */
export function describeGoogleError(status, body, apiLabel) {
  const error = body?.error || {};
  const message = String(error.message || "");
  const reason = error.details?.[0]?.reason || error.status || "";

  if (/SERVICE_DISABLED/i.test(reason) || /has not been used in project|is disabled/i.test(message)) {
    // Anchored to the console's own https origin: this url is pulled out of an
    // error message and goes straight into an href, so the pattern is the guard.
    const enableUrl = /https:\/\/console\.cloud\.google\.com\/\S*/
      .exec(message)?.[0]
      ?.replace(/[).,]+$/, "");
    return {
      ok: false,
      detail: `The key is valid, but the ${apiLabel} is not enabled on its project.`,
      fix: enableUrl || null,
    };
  }
  if (/API_KEY_INVALID/i.test(reason) || /API key not valid/i.test(message)) {
    return { ok: false, detail: "That is not a valid API key." };
  }
  if (/API_KEY_HTTP_REFERRER_BLOCKED|API_KEY_IP_ADDRESS_BLOCKED|blocked/i.test(`${reason} ${message}`)) {
    return {
      ok: false,
      detail: "The key's application restrictions are blocking this request - set them to None.",
    };
  }
  if (status === 429 || /RESOURCE_EXHAUSTED|quota/i.test(`${reason} ${message}`)) {
    return { ok: false, detail: "The key works, but its quota is exhausted for now." };
  }
  return { ok: false, detail: message || `HTTP ${status}` };
}

async function probe(url, apiLabel, fetchImpl, onSuccess) {
  let response;
  try {
    response = await fetchImpl(url, { headers: { Accept: "application/json" } });
  } catch (error) {
    return { ok: false, detail: `Could not reach Google: ${error?.message || error}` };
  }

  let body = null;
  try {
    body = await response.json();
  } catch {
    // an empty body on a 200 is still a pass
  }

  if (!response.ok) return describeGoogleError(response.status, body, apiLabel);
  return onSuccess(body);
}

export function testFactCheckKey(apiKey, fetchImpl = fetch) {
  if (!apiKey) return Promise.resolve({ ok: false, detail: "No key to test." });
  const url = `https://factchecktools.googleapis.com/v1alpha1/claims:search?${new URLSearchParams({
    query: "moon landing",
    languageCode: "en",
    pageSize: "1",
    key: apiKey,
  })}`;
  return probe(url, "Fact Check Tools API", fetchImpl, (body) => ({
    ok: true,
    detail: `Working - the index answered with ${(body?.claims || []).length} result(s).`,
  }));
}

export function testYouTubeKey(apiKey, fetchImpl = fetch) {
  if (!apiKey) return Promise.resolve({ ok: false, detail: "No key to test." });
  const url = `https://www.googleapis.com/youtube/v3/videos?${new URLSearchParams({
    part: "snippet",
    id: "dQw4w9WgXcQ",
    key: apiKey,
  })}`;
  return probe(url, "YouTube Data API v3", fetchImpl, (body) => ({
    ok: true,
    detail: (body?.items || []).length
      ? "Working - channel signals will use the API."
      : "The API answered, but returned nothing. The key is fine.",
  }));
}
