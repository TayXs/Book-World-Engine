/**
 * Settings page.
 *
 * Keys are written to chrome.storage.local and never leave it, except to the
 * provider they belong to. The two optional sections - Connect YouTube and the
 * AI upgrade - are inert until they are switched on.
 */

import { PROVIDERS } from "./lib/ai.js";

const FIELDS = {
  factCheckApiKey: "value",
  youtubeApiKey: "value",
  maxClaims: "number",
  autoRun: "checked",
  aiEnabled: "checked",
  aiProvider: "value",
  aiApiKey: "value",
  aiModel: "value",
};

const $ = (id) => document.getElementById(id);

function setStatus(message, isError = false) {
  const node = $("status");
  node.textContent = message;
  node.classList.toggle("error", isError);
  if (message) setTimeout(() => (node.textContent = ""), 4000);
}

function showProvider() {
  const config = PROVIDERS[$("aiProvider").value] || PROVIDERS.gemini;
  $("providerNote").textContent = config.note;
  $("keyLink").href = config.keyUrl;
  $("aiModel").placeholder = config.defaultModel;
}

function showConnection(connected) {
  $("connectState").textContent = connected ? "Connected" : "Not connected";
  $("connectState").classList.toggle("good", Boolean(connected));
  $("connectYouTube").hidden = Boolean(connected);
  $("disconnectYouTube").hidden = !connected;
}

async function load() {
  const settings = await chrome.runtime.sendMessage({ type: "wwi:get-settings" });
  for (const [id, kind] of Object.entries(FIELDS)) {
    const node = $(id);
    if (!node) continue;
    if (kind === "checked") node.checked = Boolean(settings[id]);
    else node.value = settings[id] ?? "";
  }
  showProvider();
  showConnection(settings.youtubeConnected);
}

/**
 * Anthropic and OpenAI are optional host permissions, so the extension ships
 * without the ability to talk to them. Asking here, on a click, is the only
 * moment Chrome will accept the request.
 */
async function ensureProviderAccess(provider) {
  const config = PROVIDERS[provider];
  if (!config?.host || config.host.includes("googleapis.com")) return true;
  if (await chrome.permissions.contains({ origins: [config.host] })) return true;
  return chrome.permissions.request({ origins: [config.host] });
}

async function save() {
  const patch = {};
  for (const [id, kind] of Object.entries(FIELDS)) {
    const node = $(id);
    if (!node) continue;
    if (kind === "checked") patch[id] = node.checked;
    else if (kind === "number") patch[id] = Math.max(1, Math.min(25, Number(node.value) || 10));
    else patch[id] = node.value.trim();
  }

  if (patch.aiEnabled) {
    if (!patch.aiApiKey) {
      setStatus("The AI tier needs an API key, or turn it back off.", true);
      return;
    }
    if (!(await ensureProviderAccess(patch.aiProvider))) {
      setStatus("Without access to that provider the AI tier cannot run.", true);
      return;
    }
  }

  await chrome.runtime.sendMessage({ type: "wwi:save-settings", patch });
  setStatus("Saved.");
}

$("save").addEventListener("click", () => save().catch((e) => setStatus(String(e.message || e), true)));
$("aiProvider").addEventListener("change", showProvider);

$("clearCache").addEventListener("click", async () => {
  await chrome.runtime.sendMessage({ type: "wwi:clear-cache" });
  setStatus("Cached results cleared.");
});

$("connectYouTube").addEventListener("click", async () => {
  try {
    const settings = await chrome.runtime.sendMessage({ type: "wwi:connect-youtube" });
    if (settings?.error) throw new Error(settings.error);
    showConnection(true);
    setStatus("Connected to YouTube.");
  } catch (error) {
    setStatus(String(error.message || error), true);
  }
});

$("disconnectYouTube").addEventListener("click", async () => {
  await chrome.runtime.sendMessage({ type: "wwi:disconnect-youtube" });
  showConnection(false);
  setStatus("Disconnected here. Revoke the grant in your Google account to finish.");
});

load().catch((error) => setStatus(String(error.message || error), true));
