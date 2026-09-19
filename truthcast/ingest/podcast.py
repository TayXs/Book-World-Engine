"""Podcasts: an RSS feed, an Apple Podcasts page, or a bare audio file."""

from __future__ import annotations

import re
from urllib.parse import urlparse

import httpx

from ..models import MediaSource, SourceKind
from .errors import IngestError

AUDIO_EXTENSIONS = (".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac", ".mp4", ".m4b")
_APPLE_ID = re.compile(r"podcasts\.apple\.com/.*?/id(?P<id>\d+)")


def looks_like_audio(url: str) -> bool:
    path = urlparse(url.strip()).path.lower()
    return path.endswith(AUDIO_EXTENSIONS)


async def resolve(url: str) -> tuple[MediaSource, str]:
    """Return the episode's metadata and a direct link to its audio."""
    url = url.strip()

    if looks_like_audio(url):
        name = urlparse(url).path.rsplit("/", 1)[-1] or "Audio"
        return MediaSource(kind=SourceKind.AUDIO, url=url, title=name), url

    apple = _APPLE_ID.search(url)
    if apple:
        url = await _feed_url_from_apple(apple.group("id"))

    return await _latest_episode(url)


async def _feed_url_from_apple(collection_id: str) -> str:
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(
            "https://itunes.apple.com/lookup",
            params={"id": collection_id, "entity": "podcast"},
        )
    results = (response.json() or {}).get("results") or []
    feed = results[0].get("feedUrl") if results else None
    if not feed:
        raise IngestError("Could not find an RSS feed behind that Apple Podcasts link.")
    return feed


async def _latest_episode(feed_url: str) -> tuple[MediaSource, str]:
    import feedparser

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            response = await client.get(feed_url, headers={"User-Agent": "truthcast/0.1"})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise IngestError(f"Could not open that feed: {exc}") from exc

    content_type = response.headers.get("content-type", "")
    if content_type.startswith("audio/"):
        name = urlparse(feed_url).path.rsplit("/", 1)[-1] or "Audio"
        return MediaSource(kind=SourceKind.AUDIO, url=feed_url, title=name), feed_url

    parsed = feedparser.parse(response.content)
    if not parsed.entries:
        raise IngestError(
            "No episodes found there. Paste a podcast RSS feed, an Apple Podcasts "
            "link, or a direct link to the audio file."
        )

    entry = parsed.entries[0]
    audio_url = _enclosure_url(entry)
    if not audio_url:
        raise IngestError("That feed's newest episode has no downloadable audio.")

    return (
        MediaSource(
            kind=SourceKind.PODCAST,
            url=entry.get("link") or feed_url,
            title=entry.get("title") or "Untitled episode",
            author=(parsed.feed.get("title") if parsed.feed else None),
            published_at=entry.get("published"),
            duration_seconds=_duration(entry),
            external_id=entry.get("id"),
        ),
        audio_url,
    )


def _enclosure_url(entry: object) -> str | None:
    get = entry.get if hasattr(entry, "get") else lambda *_: None  # type: ignore[assignment]
    for link in get("links") or []:
        href = link.get("href")
        if href and str(link.get("type", "")).startswith("audio/"):
            return href
    for enclosure in get("enclosures") or []:
        href = enclosure.get("href") or enclosure.get("url")
        if href:
            return href
    return None


def _duration(entry: object) -> float | None:
    get = entry.get if hasattr(entry, "get") else lambda *_: None  # type: ignore[assignment]
    raw = get("itunes_duration")
    if not raw:
        return None
    from ..models import parse_timestamp

    return parse_timestamp(str(raw))
