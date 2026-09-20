/**
 * Caption plumbing: pick a track, parse what YouTube hands back, turn cues into
 * sentences that still know when they were said.
 *
 * Nothing here touches the network or the extension APIs, so it runs in the
 * service worker and under `node --test` alike.
 */

const PREFERRED_LANGUAGES = ["en", "en-US", "en-GB"];

/** Decode the handful of entities YouTube actually emits in caption text. */
export function decodeEntities(value) {
  if (!value) return "";
  return value
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(Number(code)))
    .replace(/&#x([0-9a-f]+);/gi, (_, code) => String.fromCharCode(parseInt(code, 16)))
    .replace(/&apos;|&#39;/g, "'");
}

/**
 * Choose a caption track. A human-written English track beats an auto-generated
 * one; an auto-generated English track beats a human-written Portuguese one,
 * because the claim heuristics downstream are English-only.
 */
export function pickTrack(tracks, languages = PREFERRED_LANGUAGES) {
  if (!Array.isArray(tracks) || tracks.length === 0) return null;
  const wanted = languages.map((l) => l.toLowerCase());

  const rank = (track) => {
    const code = String(track.languageCode || "").toLowerCase();
    const auto = track.kind === "asr";
    const exact = wanted.indexOf(code);
    const family = wanted.findIndex((l) => code.split("-")[0] === l.split("-")[0]);
    const language = exact >= 0 ? exact : family >= 0 ? family + 10 : 100;
    return language * 2 + (auto ? 1 : 0);
  };

  return [...tracks].sort((a, b) => rank(a) - rank(b))[0];
}

/** json3 is what `&fmt=json3` returns: segmented cues with millisecond offsets. */
export function parseJson3(body) {
  let data;
  try {
    data = typeof body === "string" ? JSON.parse(body) : body;
  } catch {
    return [];
  }
  const events = data && Array.isArray(data.events) ? data.events : [];
  const cues = [];
  for (const event of events) {
    if (!event || !Array.isArray(event.segs)) continue;
    const text = event.segs
      .map((seg) => (seg && typeof seg.utf8 === "string" ? seg.utf8 : ""))
      .join("")
      .replace(/\s+/g, " ")
      .trim();
    if (!text) continue;
    cues.push({
      start: (event.tStartMs || 0) / 1000,
      duration: (event.dDurationMs || 0) / 1000,
      text: decodeEntities(text),
    });
  }
  return cues;
}

/**
 * The legacy XML shape, still served when json3 is refused. Parsed with regex
 * rather than DOMParser, which does not exist in a service worker.
 */
export function parseTimedTextXml(body) {
  if (typeof body !== "string" || !body.includes("<")) return [];
  const cues = [];
  const pattern = /<text\b([^>]*)>([\s\S]*?)<\/text>/g;
  let match;
  while ((match = pattern.exec(body)) !== null) {
    const attrs = match[1];
    const start = Number(/\bstart="([\d.]+)"/.exec(attrs)?.[1] ?? 0);
    const duration = Number(/\bdur="([\d.]+)"/.exec(attrs)?.[1] ?? 0);
    const text = decodeEntities(match[2].replace(/<[^>]+>/g, " "))
      .replace(/\s+/g, " ")
      .trim();
    if (text) cues.push({ start, duration, text });
  }
  return cues;
}

/** Parse whichever of the two formats we got. */
export function parseCaptions(body) {
  const trimmed = typeof body === "string" ? body.trim() : "";
  if (!trimmed) return [];
  if (trimmed.startsWith("{")) return parseJson3(trimmed);
  return parseTimedTextXml(trimmed);
}

/**
 * Auto-captions arrive as a rolling window: each cue repeats the tail of the one
 * before it. Joining them naively triples the transcript, so drop the overlap.
 */
function dropRollingOverlap(previous, next) {
  const prev = previous.split(" ");
  const cur = next.split(" ");
  const limit = Math.min(prev.length, cur.length, 12);
  for (let size = limit; size >= 2; size--) {
    const tail = prev.slice(prev.length - size).join(" ").toLowerCase();
    const head = cur.slice(0, size).join(" ").toLowerCase();
    if (tail === head) return cur.slice(size).join(" ");
  }
  return next;
}

/**
 * Join cues into one string while remembering, for every character offset, the
 * moment it was spoken - so a claim found later can link back into the video.
 */
export function joinCues(cues) {
  const parts = [];
  const offsets = [];
  let length = 0;
  let previous = "";

  for (const cue of cues) {
    const text = (cue.text || "").replace(/\s+/g, " ").trim();
    if (!text) continue;
    const deduped = previous ? dropRollingOverlap(previous, text) : text;
    previous = text;
    if (!deduped) continue;
    if (length > 0) {
      parts.push(" ");
      length += 1;
    }
    offsets.push({ at: length, start: cue.start || 0 });
    parts.push(deduped);
    length += deduped.length;
  }

  return { text: parts.join(""), offsets };
}

/** The timestamp of whatever was being said at this character offset. */
export function timestampAt(offsets, charIndex) {
  if (!Array.isArray(offsets) || offsets.length === 0) return 0;
  let start = offsets[0].start;
  for (const entry of offsets) {
    if (entry.at > charIndex) break;
    start = entry.start;
  }
  return start;
}

/** 4:07, or 1:04:07 for the long ones. */
export function formatTimestamp(seconds) {
  const total = Math.max(0, Math.floor(seconds || 0));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const pad = (n) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`;
}

/** Ask the timedtext endpoint for json3 without mangling the signed params. */
export function withJson3(baseUrl) {
  if (!baseUrl) return baseUrl;
  return baseUrl.includes("fmt=") ? baseUrl : `${baseUrl}&fmt=json3`;
}

export { PREFERRED_LANGUAGES };
