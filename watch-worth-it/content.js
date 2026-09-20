/**
 * Watch Worth It - page side.
 *
 * Two jobs, both deliberately small: render the badge and panel into a shadow
 * root (so YouTube's stylesheet and ours never meet), and fetch youtube.com URLs
 * on the service worker's behalf, where they are same-origin and carry the
 * session the caption endpoint expects.
 */

/* --------------------------------------------------------------------- style */

const STYLE = `
:host { all: initial; }
.root {
  --fg: #0f0f0f; --muted: #606060; --line: #e3e3e3; --card: #ffffff; --chip: #f2f2f2;
  font-family: "Roboto", "Segoe UI", system-ui, sans-serif;
  display: block; margin: 8px 0 4px;
}
.root[data-theme="dark"] {
  --fg: #f1f1f1; --muted: #aaaaaa; --line: #3f3f3f; --card: #212121; --chip: #303030;
}
* { box-sizing: border-box; }
.badge {
  display: inline-flex; align-items: center; gap: 8px; cursor: pointer;
  border: 1px solid var(--line); border-radius: 999px; background: var(--card);
  color: var(--fg); padding: 5px 12px 5px 6px; font-size: 13px; line-height: 1;
}
.badge:hover { border-color: var(--muted); }
.mark {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 30px; height: 24px; padding: 0 6px; border-radius: 999px;
  font-weight: 700; font-size: 13px; color: #0f0f0f;
}
.band-green .mark { background: #7ddc9a; }
.band-yellow .mark { background: #ffd666; }
.band-red .mark { background: #ff8a80; }
.band-unverified .mark { background: #c7c7c7; }
.label { font-weight: 500; }
.chevron { color: var(--muted); font-size: 11px; }
.panel {
  margin-top: 10px; padding: 14px 16px; border: 1px solid var(--line);
  border-radius: 12px; background: var(--card); color: var(--fg);
  font-size: 13px; line-height: 1.5; max-width: 760px;
}
h3 { font-size: 13px; margin: 16px 0 8px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }
h3 .count { color: var(--fg); font-weight: 700; }
.lead { margin: 0 0 4px; }
.muted { color: var(--muted); }
.small { font-size: 12px; }
ul { list-style: none; margin: 0; padding: 0; }
.claims > li { padding: 10px 0; border-top: 1px solid var(--line); }
.claim-text { margin: 4px 0 6px; }
.stamp-link {
  background: none; border: none; padding: 0; cursor: pointer;
  color: #3ea6ff; font: inherit; font-variant-numeric: tabular-nums;
}
.chips { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 6px; }
.chip { background: var(--chip); border-radius: 4px; padding: 2px 6px; font-size: 11px; color: var(--muted); }
.match { margin-top: 6px; padding-left: 10px; border-left: 2px solid var(--line); }
.match-claim { margin: 0 0 4px; color: var(--muted); font-size: 12px; }
.rating { font-weight: 700; margin-right: 6px; }
.rating.good { color: #2ba640; }
.rating.bad { color: #d93025; }
.rating.neutral { color: var(--muted); }
.link { color: #3ea6ff; text-decoration: none; }
.link:hover { text-decoration: underline; }
.signals > li { display: grid; grid-template-columns: 110px 1fr 140px; gap: 8px; align-items: center; padding: 3px 0; }
.bar { background: var(--chip); border-radius: 999px; height: 6px; overflow: hidden; }
.fill { display: block; height: 100%; background: #3ea6ff; }
.part-detail { color: var(--muted); font-size: 12px; text-align: right; }
.warnings { margin-top: 12px; color: var(--muted); font-size: 12px; }
.warnings li { padding: 2px 0; }
.foot { display: flex; align-items: center; gap: 12px; margin-top: 14px; padding-top: 10px; border-top: 1px solid var(--line); }
.spacer { flex: 1; }
.text-button { background: none; border: none; color: var(--muted); cursor: pointer; font: inherit; padding: 0; }
.text-button:hover { color: var(--fg); text-decoration: underline; }
.stamp { margin: 8px 0 0; color: var(--muted); font-size: 11px; }
`;

const HOST_ID = "watch-worth-it-host";
const BAND_LABEL = {
  green: "Checks out so far",
  yellow: "Mixed signals",
  red: "Weak on the evidence",
  unverified: "Unverified",
};

let currentVideoId = null;
let state = { phase: "idle" };
let expanded = false;
let shadow = null;

/* --------------------------------------------------------------- fetch proxy */

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "wwi:fetch") return false;
  fetch(message.url, { credentials: "include" })
    .then(async (response) => ({
      ok: response.ok,
      status: response.status,
      body: response.ok ? await response.text() : "",
      error: response.ok ? "" : `HTTP ${response.status}`,
    }))
    .then(sendResponse)
    .catch((error) => sendResponse({ ok: false, status: 0, error: String(error?.message || error) }));
  return true;
});

/* -------------------------------------------------------------- page signals */

const text = (selector) => document.querySelector(selector)?.textContent?.trim() || "";

/** What the watch page already knows, for when no API key is configured. */
function pageSignals() {
  return {
    title: text("#above-the-fold #title h1") || text("h1.ytd-watch-metadata") || document.title.replace(/ - YouTube$/, ""),
    channelTitle: text("#upload-info #channel-name a") || text("ytd-channel-name#channel-name a"),
    subscriberText: text("#owner-sub-count"),
    viewText: text("#info-container #view-count") || text("ytd-watch-info-text #view-count"),
    dateText:
      document.querySelector("#info-container yt-formatted-string")?.textContent?.trim() ||
      text("ytd-watch-info-text"),
  };
}

function videoIdFromLocation() {
  const id = new URLSearchParams(location.search).get("v");
  return id && /^[A-Za-z0-9_-]{11}$/.test(id) ? id : null;
}

/* ------------------------------------------------------------------- mounting */

function anchorNode() {
  return (
    document.querySelector("#above-the-fold #title") ||
    document.querySelector("ytd-watch-metadata #title") ||
    document.querySelector("h1.ytd-watch-metadata")?.parentElement ||
    null
  );
}

function ensureHost() {
  const anchor = anchorNode();
  if (!anchor) return null;

  let host = document.getElementById(HOST_ID);
  if (!host) {
    host = document.createElement("div");
    host.id = HOST_ID;
    shadow = host.attachShadow({ mode: "open" });
    shadow.innerHTML = `<style>${STYLE}</style><div class="root"></div>`;
  }
  if (host.parentElement !== anchor) anchor.appendChild(host);
  shadow = host.shadowRoot;
  shadow.querySelector(".root").dataset.theme = document.documentElement.hasAttribute("dark")
    ? "dark"
    : "light";
  return host;
}

/* ------------------------------------------------------------------- analysis */

async function run({ force = false } = {}) {
  const videoId = videoIdFromLocation();
  if (!videoId) return;
  currentVideoId = videoId;

  setState({ phase: "loading" });
  try {
    const result = await chrome.runtime.sendMessage({
      type: "wwi:analyze",
      videoId,
      pageSignals: pageSignals(),
      force,
    });
    if (currentVideoId !== videoId) return; // the user moved on mid-flight
    if (!result || result.status === "error") {
      setState({ phase: "error", error: result?.error || "analysis failed" });
      return;
    }
    setState({ phase: "ready", result });
  } catch (error) {
    // "Extension context invalidated" after a reload is expected; stay quiet.
    setState({ phase: "error", error: String(error?.message || error) });
  }
}

function setState(next) {
  state = next;
  render();
}

/* -------------------------------------------------------------------- render */

function render() {
  const host = ensureHost();
  if (!host || !shadow) return;
  const root = shadow.querySelector(".root");
  root.innerHTML = `${renderBadge()}${expanded ? renderPanel() : ""}`;
  wire(root);
}

function renderBadge() {
  if (state.phase === "loading") {
    return badgeHtml("unverified", "···", "Reading the transcript");
  }
  if (state.phase === "error") {
    return badgeHtml("unverified", "!", "Watch Worth It failed");
  }
  if (state.phase === "manual") {
    return `<button class="badge band-unverified" type="button" data-action="check">
      <span class="mark">▶</span><span class="label">Check this video</span></button>`;
  }
  if (state.phase !== "ready") return "";

  const { result } = state;
  if (result.status === "no-transcript") {
    return badgeHtml("unverified", "–", "No transcript available");
  }
  if (result.unverified || result.score === null) {
    return badgeHtml("unverified", "?", "Unverified — no fact-check data");
  }
  return badgeHtml(result.band, String(result.score), BAND_LABEL[result.band] || "");
}

function badgeHtml(bandName, value, label) {
  return `
    <button class="badge band-${bandName}" type="button" data-action="toggle"
            aria-expanded="${expanded}" title="Watch Worth It — click for the detail">
      <span class="mark">${escape(value)}</span>
      <span class="label">${escape(label)}</span>
      <span class="chevron">${expanded ? "▴" : "▾"}</span>
    </button>`;
}

function renderPanel() {
  if (state.phase === "loading") return panelShell(`<p class="muted">Pulling captions and checking claims…</p>`);
  if (state.phase === "error") {
    return panelShell(`<p class="muted">Something went wrong: ${escape(state.error)}</p>
      <p class="muted">Reload the page and try again, or check the options page.</p>`);
  }
  if (state.phase !== "ready") return "";

  const { result } = state;
  const sections = [];

  if (result.status === "no-transcript") {
    sections.push(`<p class="lead">No captions exist for this video, so there is nothing to extract claims from.</p>`);
  } else if (result.unverified) {
    sections.push(`<p class="lead">${escape(result.reason || "No published fact-check covers the claims in this video.")}</p>
      <p class="muted">That is not a verdict — most claims in most videos have never been reviewed by a fact-checking
      publisher. What is below is everything else this extension can tell you for free.</p>`);
  } else {
    sections.push(`<p class="lead">${escape(result.factCheck?.detail || "")}. Score weights published fact-checks at
      60% and channel signals at 40%.</p>`);
  }

  if (result.claims?.length) sections.push(renderClaims(result.claims));
  if (result.channel?.parts?.length) sections.push(renderChannel(result.channel, result.channelSignals));
  if (result.warnings?.length) {
    sections.push(`<ul class="warnings">${result.warnings.map((w) => `<li>${escape(w)}</li>`).join("")}</ul>`);
  }

  sections.push(`
    <div class="foot">
      <a class="link" href="${escape(result.searchUrl)}" target="_blank" rel="noreferrer noopener">
        Search Google for fact checks →</a>
      <span class="spacer"></span>
      <button class="text-button" type="button" data-action="recheck">Re-check</button>
      <button class="text-button" type="button" data-action="options">Settings</button>
    </div>
    <p class="stamp">${result.fromCache ? "Cached" : "Checked"} ${escape(shortTime(result.generatedAt))}${
      result.tier === "ai" ? " · AI tier" : ""
    }</p>`);

  return panelShell(sections.join(""));
}

function panelShell(inner) {
  return `<section class="panel">${inner}</section>`;
}

function renderClaims(claims) {
  const rows = claims
    .map((claim) => {
      const matches = (claim.matches || [])
        .map((match) => {
          const reviews = match.reviews
            .map(
              (review) => `<li><a class="link" href="${escape(review.url)}" target="_blank" rel="noreferrer noopener">
                <span class="rating ${polarityClass(review.polarity)}">${escape(review.rating || "reviewed")}</span>
                ${escape(review.publisher)}</a></li>`
            )
            .join("");
          return `<div class="match"><p class="match-claim">“${escape(match.text)}”</p><ul>${reviews}</ul></div>`;
        })
        .join("");

      const chips = (claim.signals || [])
        .map((signal) => `<span class="chip">${escape(signal)}</span>`)
        .join("");

      return `
        <li class="claim">
          <button class="stamp-link" type="button" data-action="seek" data-start="${Number(claim.start) || 0}">
            ${escape(clock(claim.start))}</button>
          <p class="claim-text">${escape(claim.text)}</p>
          <div class="chips">${chips}</div>
          ${matches || `<p class="muted small">No published fact-check matched this claim.</p>`}
        </li>`;
    })
    .join("");

  return `<h3>Claims checked <span class="count">${claims.length}</span></h3><ul class="claims">${rows}</ul>`;
}

function renderChannel(channel, signals = {}) {
  const rows = channel.parts
    .map(
      (part) => `
      <li>
        <span class="part-label">${escape(part.label)}</span>
        <span class="bar"><span class="fill" style="width:${Math.round(part.value * 100)}%"></span></span>
        <span class="part-detail">${escape(part.detail)}</span>
      </li>`
    )
    .join("");
  const source = signals.source === "youtube-data-api" ? "YouTube Data API" : "the watch page";
  return `<h3>Channel signals</h3><ul class="signals">${rows}</ul>
    <p class="muted small">Read from ${escape(source)}.</p>`;
}

/* -------------------------------------------------------------------- events */

function wire(root) {
  root.querySelectorAll("[data-action]").forEach((node) => {
    node.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const action = node.dataset.action;
      if (action === "toggle") {
        expanded = !expanded;
        render();
      } else if (action === "check") {
        expanded = true;
        run();
      } else if (action === "recheck") {
        expanded = true;
        run({ force: true });
      } else if (action === "options") {
        chrome.runtime.sendMessage({ type: "wwi:open-options" }).catch(() => {});
      } else if (action === "seek") {
        const video = document.querySelector("video");
        const start = Number(node.dataset.start) || 0;
        if (video) {
          video.currentTime = start;
          video.play?.().catch(() => {});
        }
      }
    });
  });
}

/* ------------------------------------------------------------------ utilities */

function escape(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]
  );
}

function clock(seconds) {
  const total = Math.max(0, Math.floor(Number(seconds) || 0));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = String(total % 60).padStart(2, "0");
  return h > 0 ? `${h}:${String(m).padStart(2, "0")}:${s}` : `${m}:${s}`;
}

function shortTime(iso) {
  const parsed = Date.parse(iso);
  if (Number.isNaN(parsed)) return "";
  return new Date(parsed).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function polarityClass(polarity) {
  if (polarity === null || polarity === undefined) return "neutral";
  if (polarity > 0.2) return "good";
  if (polarity < -0.2) return "bad";
  return "neutral";
}

/* ---------------------------------------------------------------- navigation */

async function onNavigate() {
  const videoId = videoIdFromLocation();
  if (!videoId) {
    document.getElementById(HOST_ID)?.remove();
    currentVideoId = null;
    return;
  }
  if (videoId === currentVideoId && state.phase === "ready") return;

  expanded = false;
  state = { phase: "idle" };
  currentVideoId = videoId;

  await waitForAnchor();
  const settings = await chrome.runtime.sendMessage({ type: "wwi:get-settings" }).catch(() => null);
  if (settings?.autoRun === false) {
    setState({ phase: "manual" });
    return;
  }
  run();
}

function waitForAnchor(timeoutMs = 10000) {
  if (anchorNode()) return Promise.resolve();
  return new Promise((resolve) => {
    const started = Date.now();
    const observer = new MutationObserver(() => {
      if (anchorNode() || Date.now() - started > timeoutMs) {
        observer.disconnect();
        resolve();
      }
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
    setTimeout(() => {
      observer.disconnect();
      resolve();
    }, timeoutMs);
  });
}

document.addEventListener("yt-navigate-finish", () => onNavigate());
window.addEventListener("popstate", () => onNavigate());
// YouTube's own event is the fast path; the poll is the safety net.
let lastHref = location.href;
setInterval(() => {
  if (location.href !== lastHref) {
    lastHref = location.href;
    onNavigate();
  }
}, 1000);

onNavigate();
