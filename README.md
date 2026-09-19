# Truthcast

Paste a YouTube link or a podcast feed. Truthcast watches or listens to it, pulls
out every claim that could be checked, researches each one against the live web,
throws away everything that does not hold up, and gives you back the survivors in
language a 10-year-old can follow — on screen, or read aloud.

The point is not the summary. The point is **what gets deleted**.

```
link ──▶ transcript ──▶ claims ──▶ research ──▶ THE BAR ──▶ plain words ──▶ voice
                                                   │
                                          most claims die here
```

---

## What it actually does

1. **Gets the words.** YouTube captions when they exist; otherwise it downloads the
   audio and transcribes it locally with Whisper. Podcasts go straight to Whisper.
2. **Finds the claims.** Statements presented as fact, each rewritten to stand on its
   own ("he said it doubled" becomes "Ford said EV sales doubled in 2024"). Opinions
   and predictions are discarded here — evidence cannot settle them.
3. **Researches each one separately.** Claude runs real web searches per claim, is
   told to hunt for the claim being *wrong*, to prefer primary sources, and to watch
   for stale numbers and quiet scope changes ("true in the US" stated as worldwide).
4. **Applies the bar.** A mechanical filter, not a vibe — see below.
5. **Writes it for a kid.** Short sentences, everyday words, concrete comparisons —
   then measures the result with Flesch-Kincaid and rewrites anything still too hard.
6. **Says it out loud.** Your browser's own voice by default, or a real TTS voice and
   a downloadable MP3 if you set a key.

## The bar

A claim only reaches you when **all** of these hold:

| Rule | Default | Why |
|---|---|---|
| Verdict is `true` or `mostly_true` | — | `unverified` never reaches you, however interesting |
| Confidence ≥ | `0.75` | the model's read of the *evidence*, not its intuition |
| Independent domains ≥ | `2` | two pages on `nih.gov` are one source, not two |
| Every citation is real | always | the verifier may only cite pages the search actually returned; invented references are dropped in code, not by asking nicely |

Claims that fail get counted, not hidden: the digest tells you how many were dropped
and why ("3 × no solid evidence either way").

**Corrections.** A claim *disproven* to the same standard is itself verified
information, and usually the most useful thing in the episode — so those appear in a
separate "what didn't hold up" section. If you want confirmed facts only, set
`TRUTHCAST_INCLUDE_CORRECTIONS=false`.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .

cp .env.example .env     # then put your key in it
```

You need an Anthropic API key (`ANTHROPIC_API_KEY`), or an `ant auth login` profile.

For podcasts and for videos without captions, add speech recognition:

```bash
pip install -e '.[asr]'   # faster-whisper + yt-dlp
```

## Use it

**Web app** — the nicer way, with the listen-along player:

```bash
truthcast-serve          # http://127.0.0.1:8000
```

**Command line:**

```bash
truthcast "https://www.youtube.com/watch?v=..."
truthcast "https://feeds.example.com/show.xml" -i health -i money
truthcast "https://youtu.be/..." --script
truthcast "https://youtu.be/..." --json > digest.json
truthcast "https://youtu.be/..." --speak          # writes an MP3
```

`-i/--interest` tells it what you care about; verified facts are ranked against
those, so the things that matter to you are read out first.

Accepted links: YouTube (watch, youtu.be, shorts, embed, live), podcast RSS feeds,
Apple Podcasts show pages, and direct audio files.

## Listening

`TRUTHCAST_TTS_PROVIDER` picks the voice:

- `browser` (default) — the web player speaks it with your device's own voice. No key,
  no cost, nothing leaves your machine. Pause, resume and speed controls included.
- `elevenlabs` — needs `ELEVENLABS_API_KEY`; produces a downloadable MP3.
- `openai` — needs `OPENAI_API_KEY`; same.

The spoken script is written separately from the page: no URLs, no "item 3 of 7", and
it ends by telling you how many claims it threw out.

## Tuning

Everything lives in `.env` (see `.env.example`). The ones worth touching:

| Setting | Default | Effect |
|---|---|---|
| `TRUTHCAST_MIN_CONFIDENCE` | `0.75` | raise for a stricter digest, lower for a fuller one |
| `TRUTHCAST_MIN_INDEPENDENT_SOURCES` | `2` | `3` is noticeably harsher |
| `TRUTHCAST_MAX_CLAIMS` | `25` | the main cost lever |
| `TRUTHCAST_EFFORT` | `high` | `medium` is cheaper and faster |
| `TRUTHCAST_TARGET_READING_GRADE` | `5.0` | `8.0` for an adult register |

**Cost.** Each claim costs two Claude calls plus its web searches, so a 25-claim
episode is roughly 50 calls — cents, not dollars, but it adds up over a whole feed.
Claim extraction runs on Sonnet (`TRUTHCAST_EXTRACTION_MODEL`) because it is bulk work
over a long transcript; verification stays on Opus, because that is the part that
decides what you are told.

## How it is put together

```
truthcast/
  ingest/        youtube captions · podcast feeds · whisper fallback
  pipeline/
    claims.py    transcript  ──▶ self-contained claims
    research.py  claim       ──▶ verdict + real citations
    gate.py      verdict     ──▶ keep or drop        ← the policy, in one file
    explain.py   kept claims ──▶ words a kid can read
    digest.py    the whole run
  llm.py         Claude wrapper: structured output, web search, pause_turn, refusals
  readability.py Flesch-Kincaid, so "simple" is measured rather than assumed
  tts.py         browser · elevenlabs · openai
  api.py         FastAPI + SSE progress
  store.py       SQLite jobs
web/             the UI — plain HTML, CSS and JS, no build step
```

Claims are researched concurrently, and one failed claim never sinks the run — it
comes back `unverified` and gets dropped like any other weak claim.

## Tests

```bash
pip install -e '.[dev]'
pytest          # 85 tests, no network, no API key needed
ruff check truthcast tests
```

The suite stubs Claude out and concentrates on the places where a mistake would mean
telling you something false: the bar (`test_gate.py`), citation integrity
(`test_research.py`), and a full pipeline run (`test_pipeline.py`).

## Honest limits

- **It is a filter, not an oracle.** It reduces what reaches you to claims with real,
  independent, current sources behind them. That is a far better diet than raw
  podcast — it is not certainty. Check the sources on anything that matters; every
  fact ships with its links and a timestamp back to the moment it was said.
- **Fresh news checks badly.** If the web has not caught up yet, the honest answer is
  `unverified`, so breaking-news episodes come back thin. That is working correctly.
- **Contested topics come back thin too,** for the same reason.
- **Simplifying can shave nuance.** The prompts forbid dropping the qualifier that
  made something true, and a rewrite is only accepted when it actually reads easier —
  but read the full explanation when the detail matters.
- **Whisper is slow on long audio** without a GPU. Captioned YouTube videos are much
  faster because there is nothing to transcribe.
