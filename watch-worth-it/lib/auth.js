/**
 * "Connect YouTube" - and nothing else.
 *
 * This module is the only place chrome.identity is touched, and it is imported
 * lazily, so a user who never flips the toggle never loads it. The token it
 * hands back is used for one thing: reading public channel statistics on the
 * free YouTube Data API quota, as an alternative to pasting an API key.
 * Transcripts and claim research never see it - they are not authenticated at
 * all, by design.
 */

export const SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"];

/** getAuthToken resolves to a string on older Chrome and an object on newer. */
function unwrap(result) {
  if (!result) return null;
  return typeof result === "string" ? result : result.token || null;
}

export async function getToken({ interactive = false } = {}) {
  try {
    return unwrap(await chrome.identity.getAuthToken({ interactive, scopes: SCOPES }));
  } catch (error) {
    if (interactive) throw new Error(describe(error));
    return null; // a silent refresh that fails is not worth reporting
  }
}

export async function connect() {
  const token = await getToken({ interactive: true });
  if (!token) throw new Error("Google did not return a token.");
  return token;
}

/**
 * Forget the token locally. Chrome has no API to revoke the grant itself, so
 * the options page also links to the Google account permissions page - saying
 * "disconnected" while the grant still exists would be a lie.
 */
export async function disconnect() {
  const token = await getToken({ interactive: false });
  if (token) await chrome.identity.removeCachedAuthToken({ token });
  await chrome.identity.clearAllCachedAuthTokens?.();
  return { revokeUrl: "https://myaccount.google.com/permissions" };
}

function describe(error) {
  const message = String(error?.message || error || "unknown error");
  if (/OAuth2 not granted or revoked|user did not approve|canceled/i.test(message)) {
    return "Sign-in was cancelled.";
  }
  if (/bad client id|invalid client|OAuth2 client id/i.test(message)) {
    return "This build has no OAuth client ID yet - see the README before connecting.";
  }
  return message;
}
