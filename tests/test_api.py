"""The HTTP surface, with the pipeline itself stubbed out."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from truthcast import api
from truthcast.config import get_settings
from truthcast.ingest.errors import IngestError
from truthcast.models import Digest, Fact, JobState, MediaSource, SourceKind


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TRUTHCAST_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    with TestClient(api.app) as test_client:
        yield test_client
    get_settings.cache_clear()


def fake_digest() -> Digest:
    return Digest(
        source=MediaSource(kind=SourceKind.YOUTUBE, url="https://x", title="An Episode"),
        intro="Here is what held up.",
        facts=[Fact(headline="Sleep helps", explanation="It really does.")],
        audio_script="Here is what held up. Sleep helps.",
        claims_examined=3,
        claims_dropped=2,
    )


def stub_pipeline(digest=None, audio=None, error=None):
    async def run(url, *, interests, speak, on_progress, settings):
        if on_progress:
            await on_progress(JobState.FETCHING, "Opening the link", 0.05)
        if error:
            raise error
        return digest or fake_digest(), audio
    return run


def wait_for(client, job_id, state, tries=200):
    for _ in range(tries):
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["state"] == state:
            return job
    raise AssertionError(f"job never reached {state}: {job}")


def test_config_tells_the_ui_where_the_bar_is(client):
    config = client.get("/api/config").json()
    assert config["min_independent_sources"] >= 1
    assert "tts_provider" in config


def test_a_job_runs_and_returns_a_digest(client, monkeypatch):
    monkeypatch.setattr(api, "run_pipeline", stub_pipeline())
    created = client.post("/api/jobs", json={"url": "https://youtu.be/abcdefghijk"})
    assert created.status_code == 202

    job = wait_for(client, created.json()["id"], "done")
    assert job["digest"]["source"]["title"] == "An Episode"
    assert job["progress"] == 1.0


def test_an_empty_url_is_rejected(client):
    assert client.post("/api/jobs", json={"url": "   "}).status_code == 400


def test_a_broken_source_fails_the_job_instead_of_hanging(client, monkeypatch):
    monkeypatch.setattr(
        api, "run_pipeline", stub_pipeline(error=IngestError("No captions anywhere."))
    )
    created = client.post("/api/jobs", json={"url": "https://youtu.be/abcdefghijk"})
    job = wait_for(client, created.json()["id"], "failed")
    assert "No captions" in job["error"]


def test_an_unexpected_crash_still_reaches_a_final_state(client, monkeypatch):
    monkeypatch.setattr(api, "run_pipeline", stub_pipeline(error=ValueError("boom")))
    created = client.post("/api/jobs", json={"url": "https://youtu.be/abcdefghijk"})
    job = wait_for(client, created.json()["id"], "failed")
    assert "boom" in job["error"]


def test_the_script_is_served_as_plain_text(client, monkeypatch):
    monkeypatch.setattr(api, "run_pipeline", stub_pipeline())
    created = client.post("/api/jobs", json={"url": "https://youtu.be/abcdefghijk"})
    job_id = created.json()["id"]
    wait_for(client, job_id, "done")
    response = client.get(f"/api/jobs/{job_id}/script")
    assert response.text.startswith("Here is what held up.")


def test_audio_is_404_when_the_browser_is_doing_the_talking(client, monkeypatch):
    monkeypatch.setattr(api, "run_pipeline", stub_pipeline(audio=None))
    created = client.post("/api/jobs", json={"url": "https://youtu.be/abcdefghijk"})
    job_id = created.json()["id"]
    wait_for(client, job_id, "done")
    assert client.get(f"/api/jobs/{job_id}/audio").status_code == 404


def test_audio_is_served_when_a_file_was_rendered(client, monkeypatch, tmp_path):
    mp3 = tmp_path / "out.mp3"
    mp3.write_bytes(b"ID3fake")
    monkeypatch.setattr(api, "run_pipeline", stub_pipeline(audio=mp3))
    created = client.post("/api/jobs", json={"url": "https://youtu.be/abcdefghijk"})
    job_id = created.json()["id"]
    wait_for(client, job_id, "done")
    response = client.get(f"/api/jobs/{job_id}/audio")
    assert response.status_code == 200 and response.content == b"ID3fake"


def test_unknown_job_is_404(client):
    assert client.get("/api/jobs/nope").status_code == 404
    assert client.get("/api/jobs/nope/events").status_code == 404


def test_progress_events_end_with_a_terminal_state(client, monkeypatch):
    monkeypatch.setattr(api, "run_pipeline", stub_pipeline())
    created = client.post("/api/jobs", json={"url": "https://youtu.be/abcdefghijk"})
    job_id = created.json()["id"]
    with client.stream("GET", f"/api/jobs/{job_id}/events") as stream:
        payload = "".join(chunk for chunk in stream.iter_text())
    assert '"state": "done"' in payload or '"state":"done"' in payload


def test_history_lists_finished_jobs(client, monkeypatch):
    monkeypatch.setattr(api, "run_pipeline", stub_pipeline())
    created = client.post("/api/jobs", json={"url": "https://youtu.be/abcdefghijk"})
    wait_for(client, created.json()["id"], "done")
    assert len(client.get("/api/jobs").json()) == 1


def test_the_web_ui_is_served(client):
    page = client.get("/")
    assert page.status_code == 200 and "Truthcast" in page.text
