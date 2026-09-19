"""Turn a link into a transcript, whatever kind of link it is."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from ..models import SourceKind, Transcript
from . import podcast, youtube
from .errors import IngestError, TranscriptUnavailable
from .transcribe import transcribe_media

log = logging.getLogger(__name__)

Progress = Callable[[str, float], Awaitable[None] | None]


def classify(url: str) -> SourceKind:
    url = url.strip()
    if youtube.video_id(url):
        return SourceKind.YOUTUBE
    if podcast.looks_like_audio(url):
        return SourceKind.AUDIO
    return SourceKind.PODCAST


async def fetch_transcript(url: str, on_progress: Progress | None = None) -> Transcript:
    """Captions when they exist, speech recognition when they do not."""

    async def note(message: str, progress: float) -> None:
        if on_progress is not None:
            result = on_progress(message, progress)
            if result is not None:
                await result

    kind = classify(url)

    if kind is SourceKind.YOUTUBE:
        source = await youtube.fetch_metadata(url)
        await note(f"Reading captions for “{source.title}”", 0.15)
        try:
            return await youtube.fetch_captions(source)
        except TranscriptUnavailable as exc:
            log.info("no captions for %s (%s); falling back to audio", url, exc)
            await note("No captions on this one - listening to the audio instead", 0.2)
            return await transcribe_media(source, on_progress=on_progress)

    source, audio_url = await podcast.resolve(url)
    await note(f"Listening to “{source.title}”", 0.15)
    return await transcribe_media(source, audio_url=audio_url, on_progress=on_progress)


__all__ = [
    "IngestError",
    "TranscriptUnavailable",
    "classify",
    "fetch_transcript",
    "podcast",
    "youtube",
]
