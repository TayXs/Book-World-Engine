"""HTTP surface: submit a link, watch it work, read or hear the result."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .ingest.errors import IngestError
from .llm import LLMError
from .models import Job, JobRequest, JobState
from .pipeline import run as run_pipeline
from .store import JobStore
from .tts import TTSError

log = logging.getLogger(__name__)

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
POLL_SECONDS = 1.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    store = JobStore(settings.db_path)
    stale = await asyncio.to_thread(store.reset_running_sync)
    if stale:
        log.info("marked %s interrupted job(s) as failed", stale)
    app.state.store = store
    app.state.settings = settings
    app.state.tasks = set()
    yield
    for task in list(app.state.tasks):
        task.cancel()


app = FastAPI(title="Truthcast", version="0.1.0", lifespan=lifespan)


@app.get("/api/config")
async def read_config() -> dict:
    settings = app.state.settings
    return {
        "tts_provider": settings.tts_provider,
        "server_audio": settings.tts_provider != "browser",
        "min_confidence": settings.min_confidence,
        "min_independent_sources": settings.min_independent_sources,
        "include_corrections": settings.include_corrections,
        "target_reading_grade": settings.target_reading_grade,
    }


@app.post("/api/jobs", status_code=202)
async def create_job(request: JobRequest) -> Job:
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Paste a link first.")

    job = Job(
        id=uuid.uuid4().hex[:12],
        url=url,
        state=JobState.QUEUED,
        message="Queued",
        interests=[i.strip() for i in request.interests if i.strip()],
    )
    await app.state.store.save(job)

    task = asyncio.create_task(_process(job.id, request.speak))
    app.state.tasks.add(task)
    task.add_done_callback(app.state.tasks.discard)
    return job


@app.get("/api/jobs")
async def list_jobs(limit: int = 20) -> list[Job]:
    return await app.state.store.recent(limit=min(limit, 100))


@app.get("/api/jobs/{job_id}")
async def read_job(job_id: str) -> Job:
    return await _require(job_id)


@app.get("/api/jobs/{job_id}/script", response_class=PlainTextResponse)
async def read_script(job_id: str) -> str:
    job = await _require(job_id)
    if not job.digest:
        raise HTTPException(status_code=409, detail="Not finished yet.")
    return job.digest.audio_script


@app.get("/api/jobs/{job_id}/audio")
async def read_audio(job_id: str) -> FileResponse:
    job = await _require(job_id)
    if not job.audio_path or not Path(job.audio_path).exists():
        raise HTTPException(
            status_code=404,
            detail="No audio file for this job - the browser voice speaks it instead.",
        )
    return FileResponse(job.audio_path, media_type="audio/mpeg", filename=f"{job_id}.mp3")


@app.get("/api/jobs/{job_id}/events")
async def stream_events(job_id: str) -> StreamingResponse:
    await _require(job_id)

    async def events():
        last = None
        while True:
            job = await app.state.store.get(job_id)
            if job is None:
                break
            snapshot = (job.state, round(job.progress, 3), job.message)
            if snapshot != last:
                last = snapshot
                payload = {
                    "state": job.state.value,
                    "progress": job.progress,
                    "message": job.message,
                    "error": job.error,
                }
                yield f"data: {json.dumps(payload)}\n\n"
            if job.state in (JobState.DONE, JobState.FAILED):
                break
            await asyncio.sleep(POLL_SECONDS)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _require(job_id: str) -> Job:
    job = await app.state.store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="No such job.")
    return job


async def _process(job_id: str, speak: bool) -> None:
    store: JobStore = app.state.store
    settings = app.state.settings

    async def on_progress(state: JobState, message: str, progress: float) -> None:
        job = await store.get(job_id)
        if job is None:
            return
        job.state, job.message, job.progress = state, message, progress
        await store.save(job)

    try:
        job = await store.get(job_id)
        if job is None:
            return
        digest, audio_path = await run_pipeline(
            job.url,
            interests=job.interests,
            speak=speak,
            on_progress=on_progress,
            settings=settings,
        )
        job = await store.get(job_id) or job
        job.digest = digest
        job.audio_path = str(audio_path) if audio_path else None
        job.state = JobState.DONE
        job.progress = 1.0
        job.message = "Ready"
        await store.save(job)
    except (IngestError, LLMError, TTSError) as exc:
        await _fail(store, job_id, str(exc))
    except asyncio.CancelledError:
        await _fail(store, job_id, "Cancelled.")
        raise
    except Exception as exc:  # the job must always reach a final state
        log.exception("job %s crashed", job_id)
        await _fail(store, job_id, f"Unexpected error: {exc}")


async def _fail(store: JobStore, job_id: str, message: str) -> None:
    job = await store.get(job_id)
    if job is None:
        return
    job.state = JobState.FAILED
    job.error = message
    job.message = "Failed"
    await store.save(job)


if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
