/* Truthcast web client: submit a link, follow progress over SSE, read or listen. */
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const el = {
    form: $("job-form"), url: $("url"), interests: $("interests"), speak: $("speak"),
    submit: $("submit"), barNote: $("bar-note"),
    progress: $("progress"), fill: $("progress-fill"), message: $("progress-message"),
    error: $("error"), result: $("result"),
    title: $("source-title"), byline: $("source-byline"), intro: $("intro"),
    facts: $("facts"), corrections: $("corrections"),
    factsHeading: $("facts-heading"), correctionsHeading: $("corrections-heading"),
    tally: $("tally"), play: $("play"), stop: $("stop"), rate: $("rate"),
    voice: $("voice"), download: $("download"), audio: $("audio"),
    history: $("history"), historyWrap: $("history-wrap"),
  };

  let stream = null;
  const speech = { script: "", chunks: [], index: 0, voices: [], playing: false };

  /* ---------------------------------------------------------------- setup */

  async function init() {
    loadVoices();
    await showConfig();
    await loadHistory();
    el.form.addEventListener("submit", onSubmit);
    el.play.addEventListener("click", onPlay);
    el.stop.addEventListener("click", stopSpeaking);
    el.rate.addEventListener("change", () => { if (speech.playing) restartSpeech(); });
    window.addEventListener("beforeunload", () => window.speechSynthesis?.cancel());
  }

  async function showConfig() {
    try {
      const config = await fetch("/api/config").then((r) => r.json());
      el.barNote.textContent =
        `A claim is only passed on when the evidence is at least ` +
        `${Math.round(config.min_confidence * 100)}% convincing and comes from ` +
        `${config.min_independent_sources}+ independent sites. ` +
        `Everything else is dropped.`;
      el.speak.parentElement.classList.toggle("hidden", !config.server_audio);
    } catch {
      /* config is decoration; the app works without it */
    }
  }

  /* --------------------------------------------------------------- submit */

  async function onSubmit(event) {
    event.preventDefault();
    stopSpeaking();
    hide(el.error);
    hide(el.result);
    el.submit.disabled = true;

    const body = {
      url: el.url.value.trim(),
      interests: el.interests.value.split(",").map((s) => s.trim()).filter(Boolean),
      speak: el.speak.checked,
    };

    try {
      const response = await fetch("/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error((await detail(response)) || "Could not start.");
      const job = await response.json();
      show(el.progress);
      setProgress(0.02, "Queued");
      follow(job.id);
    } catch (err) {
      fail(err.message);
    }
  }

  function follow(jobId) {
    if (stream) stream.close();
    stream = new EventSource(`/api/jobs/${jobId}/events`);

    stream.onmessage = async (event) => {
      const data = JSON.parse(event.data);
      setProgress(data.progress, data.message);
      if (data.state === "failed") {
        stream.close();
        fail(data.error || "Something went wrong.");
      } else if (data.state === "done") {
        stream.close();
        const job = await fetch(`/api/jobs/${jobId}`).then((r) => r.json());
        renderJob(job);
        el.submit.disabled = false;
        hide(el.progress);
        loadHistory();
      }
    };

    // If the stream drops, fall back to polling rather than hanging forever.
    stream.onerror = () => {
      stream.close();
      pollUntilDone(jobId);
    };
  }

  async function pollUntilDone(jobId) {
    try {
      const job = await fetch(`/api/jobs/${jobId}`).then((r) => r.json());
      setProgress(job.progress, job.message);
      if (job.state === "done") {
        renderJob(job);
        hide(el.progress);
        el.submit.disabled = false;
        loadHistory();
        return;
      }
      if (job.state === "failed") return fail(job.error || "Something went wrong.");
      setTimeout(() => pollUntilDone(jobId), 2000);
    } catch (err) {
      fail(err.message);
    }
  }

  /* --------------------------------------------------------------- render */

  function renderJob(job) {
    const digest = job.digest;
    if (!digest) return fail("The job finished without a digest.");

    el.title.textContent = digest.source.title;
    el.byline.textContent = [digest.source.author, sourceLabel(digest.source.kind)]
      .filter(Boolean).join(" · ");
    el.intro.textContent = digest.intro;

    renderFacts(el.facts, digest.facts);
    renderFacts(el.corrections, digest.corrections);
    el.factsHeading.classList.toggle("hidden", digest.facts.length === 0);
    el.correctionsHeading.classList.toggle("hidden", digest.corrections.length === 0);

    el.tally.innerHTML = tallyHtml(digest);
    speech.script = digest.audio_script || "";
    setupAudio(job);
    show(el.result);
    el.result.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderFacts(container, facts) {
    container.innerHTML = "";
    for (const fact of facts) {
      const card = document.createElement("article");
      card.className = `card fact${fact.kind === "correction" ? " correction" : ""}`;

      const meta = [
        `<span class="tag ${fact.kind === "correction" ? "bad" : "good"}">${
          fact.kind === "correction" ? "Not true" : "Checks out"
        }</span>`,
        `<span>${Math.round(fact.confidence * 100)}% sure</span>`,
        `<span>${fact.sources.length} source${fact.sources.length === 1 ? "" : "s"}</span>`,
      ];
      if (fact.said_at) {
        meta.push(fact.moment_url
          ? `<a href="${escapeAttr(fact.moment_url)}" target="_blank" rel="noopener">heard at ${escapeHtml(fact.said_at)}</a>`
          : `<span>heard at ${escapeHtml(fact.said_at)}</span>`);
      }

      card.innerHTML =
        `<div class="meta">${meta.join("")}</div>` +
        `<h4>${escapeHtml(fact.headline)}</h4>` +
        `<p>${escapeHtml(fact.explanation)}</p>` +
        (fact.real_world_link
          ? `<p class="matters"><strong>What it means for you:</strong> ${escapeHtml(fact.real_world_link)}</p>`
          : "") +
        (fact.sources.length
          ? `<ul class="sources">${fact.sources.map(sourceLine).join("")}</ul>`
          : "");
      container.appendChild(card);
    }
  }

  const sourceLine = (source) =>
    `<li><a href="${escapeAttr(source.url)}" target="_blank" rel="noopener noreferrer">${
      escapeHtml(source.title || source.url)
    }</a></li>`;

  function tallyHtml(digest) {
    const kept = digest.facts.length + digest.corrections.length;
    const reasons = Object.entries(digest.dropped_reasons || {})
      .map(([reason, count]) => `<li>${count} × ${escapeHtml(reason)}</li>`)
      .join("");
    return (
      `<strong>${kept} of ${digest.claims_examined}</strong> claims made it through. ` +
      `${digest.claims_dropped} were dropped.` +
      (reasons ? `<ul>${reasons}</ul>` : "") +
      `<p style="margin:10px 0 0">Written at about a grade ${digest.reading_grade} reading level.</p>`
    );
  }

  const sourceLabel = (kind) =>
    ({ youtube: "YouTube", podcast: "Podcast", audio: "Audio file", text: "Text" })[kind] || kind;

  /* ---------------------------------------------------------------- audio */

  function setupAudio(job) {
    const hasFile = Boolean(job.audio_path);
    el.audio.classList.toggle("hidden", !hasFile);
    el.download.classList.toggle("hidden", !hasFile);
    if (hasFile) {
      el.audio.src = `/api/jobs/${job.id}/audio`;
      el.download.href = `/api/jobs/${job.id}/audio`;
    }
    const canSpeak = "speechSynthesis" in window && speech.script;
    el.play.classList.toggle("hidden", !canSpeak);
    el.rate.parentElement.classList.toggle("hidden", !canSpeak);
    el.voice.classList.toggle("hidden", !canSpeak || el.voice.options.length === 0);
  }

  function loadVoices() {
    if (!("speechSynthesis" in window)) return;
    const fill = () => {
      const voices = window.speechSynthesis.getVoices().filter((v) => v.lang.startsWith("en"));
      el.voice.innerHTML = voices
        .map((v, i) => `<option value="${i}">${escapeHtml(v.name)}</option>`)
        .join("");
      speech.voices = voices;
    };
    fill();
    window.speechSynthesis.onvoiceschanged = fill;
  }

  function onPlay() {
    if (speech.playing) {
      window.speechSynthesis.pause();
      speech.playing = false;
      el.play.textContent = "▶ Resume";
      return;
    }
    if (window.speechSynthesis.paused && speech.index > 0) {
      window.speechSynthesis.resume();
      speech.playing = true;
      el.play.textContent = "❚❚ Pause";
      return;
    }
    startSpeech();
  }

  function startSpeech() {
    // Long utterances get cut off in some browsers, so speak paragraph by
    // paragraph and keep our own queue.
    speech.chunks = speech.script.split(/\n{2,}/).map((s) => s.trim()).filter(Boolean);
    speech.index = 0;
    window.speechSynthesis.cancel();
    speech.playing = true;
    el.play.textContent = "❚❚ Pause";
    show(el.stop);
    speakNext();
  }

  function speakNext() {
    if (speech.index >= speech.chunks.length) return stopSpeaking();
    const utterance = new SpeechSynthesisUtterance(speech.chunks[speech.index]);
    utterance.rate = parseFloat(el.rate.value) || 1;
    const chosen = speech.voices?.[parseInt(el.voice.value, 10)];
    if (chosen) utterance.voice = chosen;
    utterance.onend = () => {
      speech.index += 1;
      if (speech.playing) speakNext();
    };
    utterance.onerror = () => stopSpeaking();
    window.speechSynthesis.speak(utterance);
  }

  function restartSpeech() {
    const resumeAt = speech.index;
    window.speechSynthesis.cancel();
    speech.index = resumeAt;
    speakNext();
  }

  function stopSpeaking() {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    speech.playing = false;
    speech.index = 0;
    el.play.textContent = "▶ Listen";
    hide(el.stop);
  }

  /* -------------------------------------------------------------- history */

  async function loadHistory() {
    try {
      const jobs = await fetch("/api/jobs?limit=8").then((r) => r.json());
      const done = jobs.filter((job) => job.state === "done" && job.digest);
      if (!done.length) return hide(el.historyWrap);
      el.history.innerHTML = done
        .map(
          (job) =>
            `<li><a href="#" data-job="${escapeAttr(job.id)}">${escapeHtml(
              job.digest.source.title
            )}</a> — ${job.digest.facts.length} verified, ${job.digest.claims_dropped} dropped</li>`
        )
        .join("");
      el.history.querySelectorAll("a[data-job]").forEach((link) =>
        link.addEventListener("click", async (event) => {
          event.preventDefault();
          stopSpeaking();
          const job = await fetch(`/api/jobs/${link.dataset.job}`).then((r) => r.json());
          renderJob(job);
        })
      );
      show(el.historyWrap);
    } catch {
      hide(el.historyWrap);
    }
  }

  /* --------------------------------------------------------------- helpers */

  function setProgress(value, message) {
    el.fill.style.width = `${Math.max(2, Math.round((value || 0) * 100))}%`;
    el.message.textContent = message || "Working…";
  }

  function fail(message) {
    el.error.textContent = message;
    show(el.error);
    hide(el.progress);
    el.submit.disabled = false;
  }

  async function detail(response) {
    try {
      return (await response.json()).detail;
    } catch {
      return null;
    }
  }

  const show = (node) => node.classList.remove("hidden");
  const hide = (node) => node.classList.add("hidden");

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]
    );
  }
  const escapeAttr = escapeHtml;

  // Last statement in the module: every binding above is initialised by now.
  init();
})();
