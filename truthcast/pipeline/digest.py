"""The whole run: link in, verified digest out."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

from ..config import Settings, get_settings
from ..ingest import fetch_transcript
from ..llm import ClaudeClient
from ..models import Assessment, Digest, JobState, MediaSource, Transcript
from .claims import extract_claims
from .explain import write_digest
from .gate import partition
from .research import verify_all

log = logging.getLogger(__name__)

Progress = Callable[[JobState, str, float], Awaitable[None] | None]


async def _report(on_progress: Progress | None, state: JobState, message: str, pct: float):
    if on_progress is None:
        return
    result = on_progress(state, message, pct)
    if result is not None:
        await result


async def build_digest(
    transcript: Transcript,
    *,
    client: ClaudeClient,
    settings: Settings,
    interests: list[str] | None = None,
    on_progress: Progress | None = None,
) -> Digest:
    """Everything after the transcript exists - the part worth testing offline."""
    source: MediaSource = transcript.source

    await _report(on_progress, JobState.EXTRACTING, "Finding the checkable claims", 0.4)
    claims = await extract_claims(client, transcript, settings)
    log.info("extracted %s claims from %s", len(claims), source.title)

    if not claims:
        return await write_digest(
            client, source, [], settings, interests=interests, examined=0, dropped={}
        )

    await _report(
        on_progress,
        JobState.RESEARCHING,
        f"Checking {len(claims)} claims against real sources",
        0.45,
    )

    async def claim_done(done: int, total: int, assessment: Assessment) -> None:
        await _report(
            on_progress,
            JobState.RESEARCHING,
            f"Checked {done} of {total}: {assessment.verdict.value.replace('_', ' ')}",
            0.45 + 0.4 * (done / max(1, total)),
        )

    assessments = await verify_all(
        client, claims, source, settings, on_done=claim_done
    )

    kept, dropped = partition(assessments, settings)
    log.info("%s of %s claims cleared the bar", len(kept), len(assessments))

    await _report(
        on_progress,
        JobState.WRITING,
        f"{len(kept)} of {len(assessments)} claims held up - writing it up",
        0.88,
    )
    return await write_digest(
        client,
        source,
        kept,
        settings,
        interests=interests,
        examined=len(assessments),
        dropped=dropped,
    )


async def run(
    url: str,
    *,
    interests: list[str] | None = None,
    speak: bool = False,
    on_progress: Progress | None = None,
    client: ClaudeClient | None = None,
    settings: Settings | None = None,
) -> tuple[Digest, Path | None]:
    settings = settings or get_settings()
    client = client or ClaudeClient(settings)

    await _report(on_progress, JobState.FETCHING, "Opening the link", 0.05)

    async def ingest_progress(message: str, pct: float) -> None:
        state = JobState.TRANSCRIBING if pct > 0.18 else JobState.FETCHING
        await _report(on_progress, state, message, pct)

    transcript = await fetch_transcript(url, on_progress=ingest_progress)
    log.info(
        "transcript: %s segments, origin=%s, %s",
        len(transcript.segments),
        transcript.origin,
        transcript.source.title,
    )

    digest = await build_digest(
        transcript,
        client=client,
        settings=settings,
        interests=interests,
        on_progress=on_progress,
    )

    audio_path: Path | None = None
    if speak and digest.audio_script:
        from ..tts import speak_text

        await _report(on_progress, JobState.SPEAKING, "Recording the audio", 0.95)
        audio_path = await speak_text(digest.audio_script, settings=settings)

    await _report(on_progress, JobState.DONE, "Ready", 1.0)
    return digest, audio_path
