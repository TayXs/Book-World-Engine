from truthcast.models import Job, JobState
from truthcast.store import JobStore


def make_store(tmp_path) -> JobStore:
    return JobStore(tmp_path / "jobs.sqlite3")


def test_a_job_survives_a_round_trip(tmp_path):
    store = make_store(tmp_path)
    store.save_sync(Job(id="a1", url="https://x", interests=["health"]))
    loaded = store.get_sync("a1")
    assert loaded.url == "https://x" and loaded.interests == ["health"]


def test_saving_again_updates_in_place(tmp_path):
    store = make_store(tmp_path)
    job = store.save_sync(Job(id="a1", url="https://x"))
    job.state, job.progress = JobState.RESEARCHING, 0.5
    store.save_sync(job)
    assert store.get_sync("a1").state is JobState.RESEARCHING
    assert len(store.recent_sync()) == 1


def test_missing_job_is_none(tmp_path):
    assert make_store(tmp_path).get_sync("nope") is None


def test_recent_jobs_come_back_newest_first(tmp_path):
    store = make_store(tmp_path)
    for index in range(3):
        job = Job(id=f"j{index}", url=f"https://x/{index}")
        job.created_at = job.created_at.replace(year=2020 + index)
        store.save_sync(job)
    assert [job.id for job in store.recent_sync()] == ["j2", "j1", "j0"]


def test_jobs_left_running_by_a_restart_are_marked_failed(tmp_path):
    store = make_store(tmp_path)
    store.save_sync(Job(id="running", url="https://x", state=JobState.RESEARCHING))
    store.save_sync(Job(id="finished", url="https://y", state=JobState.DONE))

    assert store.reset_running_sync() == 1
    assert store.get_sync("running").state is JobState.FAILED
    assert "again" in store.get_sync("running").error
    assert store.get_sync("finished").state is JobState.DONE
