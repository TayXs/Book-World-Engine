# Watch Worth It

A Chrome extension that researches a YouTube video **before** you watch it.

It reads the video's own captions, pulls out the sentences that could actually be
checked, asks Google's fact-check index whether anyone has already checked them,
reads a few signals off the channel, and puts one number next to the title.

```
video ──▶ captions ──▶ candidate claims ──▶ fact-check lookup ──┐
                          (regex, free)        (free, key only) ├─▶ 0-100
                                    channel + recency signals ──┘
```

Zero cost by default: no backend, no billing account, no model call. The one
thing worth setting up is a free Fact Check Tools API key.

---

## Install

### On a computer

1. `chrome://extensions` → enable **Developer mode** → **Load unpacked** → pick
   this `watch-worth-it/` folder.
2. Get an API key (below) and paste it into the options page, which opens on
   install. Press **Test** — it checks the key against the live API and tells you
   what is wrong if anything is.
3. Open any YouTube watch page. The badge appears next to the title.

Without a key everything still runs: you get the claims, the channel signals and
a gray **Unverified** badge, because nothing was looked up.

## Getting the API key

Free: no billing account, no credit card, no OAuth. One key covers both APIs the
extension can use.

**On a phone:** skip the script — it needs the gcloud CLI, which is not a
realistic Android install. `console.cloud.google.com` works fine in mobile
Chrome with **Desktop site** turned on (⋮ menu); follow the by-hand steps below.

**The quick way** (on a computer) — from this folder:

```bash
./setup-api-key.sh
```

It signs you in with `gcloud` if you are not already, creates a project, enables
the Fact Check Tools API and the YouTube Data API v3, creates one key restricted
to exactly those two, checks it against the live API, and prints it. It shows
you what it is about to create and waits for a yes first. Use
`--project EXISTING-ID` to add the key to a project you already have, or `--yes`
to skip the prompt. Needs the [gcloud CLI](https://cloud.google.com/sdk/docs/install).

**By hand**, if you would rather click:

1. [console.cloud.google.com](https://console.cloud.google.com/) → new project.
2. Enable
   [Fact Check Tools API](https://console.cloud.google.com/apis/library/factchecktools.googleapis.com)
   — and, optionally,
   [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com)
   on the same project, so one key does both.
3. **APIs & Services → Credentials → Create credentials → API key**.
4. Restrict it: **API restrictions** → those two APIs. Leave **Application
   restrictions** on **None** — the extension calls from a service worker, which
   sends no `Referer`, so a referrer restriction rejects every request.
5. Paste it into the options page and press **Test**.

The step people miss is 2. A key created without the API enabled comes back 403,
and the **Test** button says exactly that, with a link that enables it.

## The badge

| Badge | Meaning |
|---|---|
| 🟢 70-100 | the claims that could be checked came back supported |
| 🟡 45-69 | mixed, or thin evidence either way |
| 🔴 0-44 | published fact-checks contradict claims made in this video |
| ⚪ Unverified | **no fact-check exists for anything in this video** — not a verdict |

Gray is the common case, and it is the honest one. Most claims in most videos
have never been reviewed by a fact-checking publisher. When that happens the
panel drops the score entirely and shows what is left — channel signals, video
age, the extracted claims themselves — plus a one-click Google search for
`"<video title> fact check"` as the manual next step.

## The score

A weighted rule in one file (`lib/score.js`), not a model:

| Input | Weight | |
|---|---|---|
| Fact-check verdicts | 60% | mean publisher rating (`True` → +1 … `Pants on Fire` → −1), weighted by how well the reviewed claim matches ours |
| Channel + recency | 40% | reach 25% · channel tenure 20% · upload cadence 15% · video recency 40% |

Coverage pulls the fact-check half back toward neutral: one matched claim out of
ten cannot swing the whole score, three or more can.

## How claims are found (no model involved)

`lib/claims.js` scores every sentence and keeps the top ten:

- **up** — statistics and quantities, money, dates, cited authority ("a study
  found", "according to the FDA"), absolutes ("first", "proven", "never"),
  comparisons, cause-and-effect, named entities
- **down** — hedges ("I think", "probably", "in my opinion")
- **out** — questions, fragments, and channel boilerplate ("smash that subscribe
  button", "link in the description", "use code SAVE20")

Auto-captions arrive without punctuation and with each cue repeating the tail of
the one before it, so the transcript is de-overlapped first and cut into word
windows when there are no sentence boundaries to use. Every claim keeps the
timestamp it was spoken at, and clicking it seeks the player.

## Transcripts

Fetched client-side from YouTube's own `timedtext` endpoint — no API key, no
sign-in, no backend. The caption track list comes from the page's live
`ytInitialPlayerResponse`, falling back to the served HTML when that is stale
after an SPA navigation. The request is made by the content script, where it is
same-origin and carries the session.

No captions means no analysis: the panel says "no transcript available" and
stops. Nothing is downloaded, nothing is transcribed.

## Optional: Connect YouTube

A settings toggle, and nothing more. It signs in with Google and asks for one
read-only scope, `youtube.readonly`, so channel statistics can run on your own
free quota instead of an API key.

It never touches transcripts or claim research — those requests are
unauthenticated by design, and `chrome.identity` is reached from exactly one
lazily-imported file (`lib/auth.js`). Skip it and nothing else changes.

To make the button work in your own build you need an OAuth client ID, because
Chrome ties the grant to a specific extension ID:

1. Load the extension unpacked and copy its ID from `chrome://extensions`.
2. In the Google Cloud console, create an **OAuth client ID** of type *Chrome
   extension* with that ID, and enable the **YouTube Data API v3**.
3. Paste the client ID over `REPLACE_WITH_YOUR_OAUTH_CLIENT_ID…` in
   `manifest.json` and reload the extension.

Unpacked extensions get a fresh ID when the folder moves, which invalidates the
client. Add the packed extension's `key` to `manifest.json` if you want it to
survive.

## Optional: the AI upgrade tier

Switch on **Use AI for deeper analysis** and paste your own key — a free
[Gemini key](https://aistudio.google.com/apikey) from the same Google account,
or an Anthropic or OpenAI one.

It replaces **one step**: claim extraction. Instead of the regexes, a single
call per video extracts the claims, rewrites each to stand on its own, and says
whether it is still current — using the provider's built-in web search where
there is one (`google_search`, `web_search_20260209`, `web_search`). Everything
after that is untouched: the same fact-check lookup, the same score.

| Provider | Default model | Key |
|---|---|---|
| Google Gemini | `gemini-2.5-flash` | free tier at aistudio.google.com |
| Anthropic | `claude-opus-5` | console.anthropic.com |
| OpenAI | `gpt-5` | platform.openai.com |

Two things it does not do quietly: a transcript over 48,000 characters is
trimmed and the panel says so, and a claim whose quote cannot be found back in
the transcript is flagged rather than given a plausible timestamp. Anthropic and
OpenAI are *optional* host permissions — the extension ships unable to reach
them and asks when you save.

The default tier never loads any of this. `lib/ai.js` is imported dynamically,
only when the toggle is on and a key is set, and a failure there falls back to
the free heuristics with a warning rather than an empty panel.

## Files

```
manifest.json       MV3: storage + scripting, www + m.youtube.com, googleapis
background.js       the pipeline, end to end - the file to read first
content.js          badge and panel (shadow DOM, desktop + mobile) + fetch proxy
options.html/js     keys and toggles
lib/transcript.js   caption parsing, track choice, cue -> text with timings
lib/claims.js       the heuristics
lib/factcheck.js    Fact Check Tools API + match quality + rating polarity
lib/channel.js      YouTube Data API signals, with a watch-page fallback
lib/score.js        the 0-100 rule
lib/ytpage.js       reading the watch page
lib/store.js        settings + the per-video cache (7 days, 200 videos)
lib/auth.js         chrome.identity, lazily imported, used nowhere else
lib/ai.js           the optional tier: prompt, three providers, response parsing
lib/keytest.js      "is this key any good?", answered with a real reason
setup-api-key.sh    creates the key in your own Google Cloud account
build.sh            packs dist/watch-worth-it.zip, the Android install file
```

## Tests

```bash
node --test tests/*.test.mjs      # or: npm test
```

82 tests, no dependencies and no network. The pure modules — parsing,
heuristics, match quality, scoring — are tested directly, because those are the
places where a mistake means telling you something false about a video.

`pipeline.test.mjs` is the one that matters most: it drives the real service
worker through its own message listener with `chrome.*` and `fetch` stubbed, so
a broken wire between two individually-correct modules fails the build. It
covers the whole path — watch page to score — plus the cases that are easy to
get quietly wrong: a cache hit, a forced re-check, a stale player response, a
video with no captions, a missing API key, an unreadable page (which must not be
cached), and the AI tier both working and failing back to the free heuristics.

## Honest limits

- **The score is about coverage, not truth.** It answers "of the claims here
  that someone has already checked, how did they check out" — not "is this video
  right". A video can be wrong about everything and score gray.
- **Gray is normal.** The fact-check index is small relative to YouTube.
- **The claim heuristics are English-only** and will happily flag a sentence that
  merely sounds checkable. The panel shows you which sentences it picked and why,
  so you can see when it has grabbed the wrong thing.
- **Match quality is word overlap**, not meaning. A review of a similar-sounding
  claim is filtered out when overlap is low, which also means a genuine match
  phrased differently can be missed.
- **Channel size is weak evidence** and is weighted accordingly. A big channel is
  not a correct one.
- **The AI tier is one call, not a verification pipeline.** It finds better
  claims than the regexes do and reasons about staleness; it does not check them.
  The fact-check lookup still does that, and still usually comes back empty.
- **Keys live in `chrome.storage.local`**, unencrypted, like any extension
  setting. Anything with access to your Chrome profile can read them.
- **The mobile selectors are unverified.** They were written without a device to
  test against, which is exactly why the floating fallback exists. The pipeline
  itself is tested on both origins; where the badge *lands* on mobile is the
  part that may need a fix.
