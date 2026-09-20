/** Settings page. Keys are written to chrome.storage.local and never leave it. */

const FIELDS = {
  factCheckApiKey: "value",
  youtubeApiKey: "value",
  maxClaims: "number",
  autoRun: "checked",
};

const $ = (id) => document.getElementById(id);

function setStatus(message, isError = false) {
  const node = $("status");
  node.textContent = message;
  node.classList.toggle("error", isError);
  if (message) setTimeout(() => (node.textContent = ""), 4000);
}

async function load() {
  const settings = await chrome.runtime.sendMessage({ type: "wwi:get-settings" });
  for (const [id, kind] of Object.entries(FIELDS)) {
    const node = $(id);
    if (!node) continue;
    if (kind === "checked") node.checked = Boolean(settings[id]);
    else node.value = settings[id] ?? "";
  }
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
  await chrome.runtime.sendMessage({ type: "wwi:save-settings", patch });
  setStatus("Saved.");
}

$("save").addEventListener("click", () => save().catch((e) => setStatus(String(e.message || e), true)));
$("clearCache").addEventListener("click", async () => {
  await chrome.runtime.sendMessage({ type: "wwi:clear-cache" });
  setStatus("Cached results cleared.");
});

load().catch((error) => setStatus(String(error.message || error), true));
