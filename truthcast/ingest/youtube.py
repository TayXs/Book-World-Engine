"""YouTube: identify the video, grab its captions."""

from __future__ import annotations

import asyncio
import re

import httpx

from ..models import MediaSource, SourceKind, Transcript, TranscriptSegment
from .errors import IngestError, TranscriptUnavailable

_ID = r"(?P<id>[A-Za-z0-9_-]{11})"
_PATTERNS = [
    re.compile(r"(?:youtube\.com|youtube-nocookie\.com)/watch\?(?:[^&]*&)*v=" + _ID),
    re.compile(r"youtu\.be/" + _ID),
    re.compile(r"youtube\.com/(?:embed|shorts|live|v)/" + _ID),
]

PREFERRED_LANGUAGES = ("en", "en-US", "en-GB")


def video_id(url: str) -> str | None:
    url = url.strip()
    for pattern in _PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group("id")
    if re.fullmatch(_ID, url):  # a bare id is a fine thing to paste
        return url
    return None


async def fetch_metadata(url: str) -> MediaSource:
    """Title and channel via oEmbed - no API key, no quota."""
    vid = video_id(url)
    if not vid:
        raise IngestError(f"That does not look like a YouTube link: {url}")

    canonical = f"https://www.youtube.com/watch?v={vid}"
    title, author = f"YouTube video {vid}", None
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(
                "https://www.youtube.com/oembed",
                params={"url": canonical, "format": "json"},
            )
            if response.status_code == 200:
                data = response.json()
                title = data.get("title") or title
                author = data.get("author_name")
    except httpx.HTTPError:
        pass  # metadata is a nicety; the transcript is the point

    return MediaSource(
        kind=SourceKind.YOUTUBE, url=canonical, title=title, author=author, external_id=vid
    )


async def fetch_captions(source: MediaSource) -> Transcript:
    if not source.external_id:
        raise IngestError("Missing YouTube video id.")
    return await asyncio.to_thread(_fetch_captions_sync, source)


def _fetch_captions_sync(source: MediaSource) -> Transcript:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import CouldNotRetrieveTranscript

    api = YouTubeTranscriptApi()
    try:
        fetched = api.fetch(source.external_id, languages=PREFERRED_LANGUAGES)
    except CouldNotRetrieveTranscript as exc:
        # Disabled, absent, age-gated or IP-blocked - all mean "use the audio".
        raise TranscriptUnavailable(str(exc)) from exc

    segments: list[TranscriptSegment] = []
    for snippet in fetched:
        start = float(getattr(snippet, "start", 0.0))
        duration = float(getattr(snippet, "duration", 0.0) or 0.0)
        text = (getattr(snippet, "text", "") or "").replace("\n", " ").strip()
        if text:
            segments.append(TranscriptSegment(start=start, end=start + duration, text=text))

    if not segments:
        raise TranscriptUnavailable("Captions were empty.")

    if segments and source.duration_seconds is None:
        source = source.model_copy(update={"duration_seconds": segments[-1].end})

    return Transcript(
        source=source,
        segments=segments,
        language=getattr(fetched, "language_code", "en") or "en",
        origin="captions",
    )
