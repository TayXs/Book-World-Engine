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

1. `chrome://extensions` → enable **Developer mode** → **Load unpacked** → pick
   this `watch-worth-it/` folder.
2. The options page opens on install. Paste a
   [Fact Check Tools API key](https://console.cloud.google.com/apis/library/factchecktools.googleapis.com)
   — free, no billing account, no OAuth.
3. Open any YouTube watch page. The badge appears next to the title.

Without a key everything still runs: you get the claims, the channel signals and
a gray **Unverified** badge, because nothing was looked up.

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

## Files

```
manifest.json       MV3: storage + scripting, youtube.com + googleapis.com
background.js       the pipeline, end to end - the file to read first
content.js          badge and panel (shadow DOM) + same-origin fetch proxy
options.html/js     keys and toggles
lib/transcript.js   caption parsing, track choice, cue -> text with timings
lib/claims.js       the heuristics
lib/factcheck.js    Fact Check Tools API + match quality + rating polarity
lib/channel.js      YouTube Data API signals, with a watch-page fallback
lib/score.js        the 0-100 rule
lib/ytpage.js       reading the watch page
lib/store.js        settings + the per-video cache (7 days, 200 videos)
```

## Tests

```bash
node --test tests/*.test.mjs      # or: npm test
```

No dependencies and no network: the pure modules — parsing, heuristics, match
quality, scoring — are tested directly, because those are the places where a
mistake means telling you something false about a video.

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
