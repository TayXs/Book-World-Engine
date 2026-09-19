"""Speech recognition for anything without usable captions."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

import httpx

from ..config import get_settings
from ..models import MediaSource, SourceKind, Transcript, TranscriptSegment
from .errors import IngestError

log = logging.getLogger(__name__)

Progress = Callable[[str, float], Awaitable[None] | None]

WHISPER_MODEL = "base.en"
_MISSING_EXTRAS = (
    "This source has no captions, so it needs speech recognition. "
    "Install the extras first:  pip install -e '.[asr]'"
)


async def transcribe_media(
    source: MediaSource,
    audio_url: str | None = None,
    on_progress: Progress | None = None,
) -> Transcript:
    async def note(message: str, progress: float) -> None:
        if on_progress is not None:
            result = on_progress(message, progress)
            if result is not None:
                await result

    settings = get_settings()
    settings.ensure_dirs()

    await note("Downloading the audio", 0.22)
    if source.kind is SourceKind.YOUTUBE:
        path = await asyncio.to_thread(_download_youtube_audio, source, settings.media_dir)
    else:
        if not audio_url:
            raise IngestError("No audio URL to download.")
        path = await _download_file(audio_url, settings.media_dir, source.external_id or "episode")

    await note("Listening and writing down what was said", 0.3)
    segments, language = await asyncio.to_thread(_run_whisper, path)

    if not segments:
        raise IngestError("Speech recognition produced nothing - the audio may be silent.")

    updated = source
    if source.duration_seconds is None:
        updated = source.model_copy(update={"duration_seconds": segments[-1].end})

    return Transcript(source=updated, segments=segments, language=language, origin="asr")


async def _download_file(url: str, directory: Path, stem: str) -> Path:
    suffix = Path(url.split("?")[0]).suffix or ".mp3"
    target = directory / f"{_safe(stem)}{suffix}"
    try:
        async with (
            httpx.AsyncClient(timeout=None, follow_redirects=True) as client,
            client.stream("GET", url, headers={"User-Agent": "truthcast/0.1"}) as response,
        ):
            response.raise_for_status()
            with target.open("wb") as handle:
                async for chunk in response.aiter_bytes(chunk_size=1 << 16):
                    handle.write(chunk)
    except httpx.HTTPError as exc:
        raise IngestError(f"Could not download the audio: {exc}") from exc
    return target


def _download_youtube_audio(source: MediaSource, directory: Path) -> Path:
    try:
        import yt_dlp
    except ImportError as exc:
        raise IngestError(_MISSING_EXTRAS) from exc

    target = directory / f"{_safe(source.external_id or 'video')}.%(ext)s"
    options = {
        "format": "bestaudio/best",
        "outtmpl": str(target),
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(source.url, download=True)
        return Path(ydl.prepare_filename(info))


def _run_whisper(path: Path) -> tuple[list[TranscriptSegment], str]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise IngestError(_MISSING_EXTRAS) from exc

    model = WhisperModel(WHISPER_MODEL, device="auto", compute_type="int8")
    raw_segments, info = model.transcribe(str(path), vad_filter=True)

    segments = [
        TranscriptSegment(start=float(s.start), end=float(s.end), text=s.text.strip())
        for s in raw_segments
        if s.text and s.text.strip()
    ]
    return segments, getattr(info, "language", "en") or "en"


def _safe(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:80] or "media"
