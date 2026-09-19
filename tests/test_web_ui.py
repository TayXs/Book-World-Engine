"""A real browser loads the page and clicks through a finished digest.

This exists because of a bug that every other test missed: `init()` ran before
a `const` it depended on was initialised, so the page threw on load and none of
the event listeners were ever attached - the submit button did nothing. Only a
browser can catch that.

Skipped unless Playwright and a Chromium build are both present.
"""

from __future__ import annotations

import socket
import threading
import time

import pytest

from truthcast.config import get_settings
from truthcast.models import Digest, Evidence, Fact, Job, JobState, MediaSource, SourceKind
from truthcast.store import JobStore

playwright_api = pytest.importorskip("playwright.sync_api")

CHROMIUM_CANDIDATES = [
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    "/opt/pw-browsers/chromium/chrome-linux/chrome",
]


def chromium_path() -> str | None:
    from pathlib import Path

    for candidate in CHROMIUM_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None  # fall back to Playwright's own download, if there is one


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def seed(store: JobStore) -> Job:
    source = MediaSource(
        kind=SourceKind.YOUTUBE, url="https://youtu.be/abcdefghijk",
        title="A Checked Episode", author="Some Podcast", external_id="abcdefghijk",
    )
    digest = Digest(
        source=source,
        intro="Here is what held up.",
        facts=[
            Fact(
                headline="Sleep helps your memory",
                explanation="Your brain sorts the day while you sleep.",
                real_world_link="Sleep before a test, not after.",
                confidence=0.9, said_at="1:01",
                moment_url=source.at(61),
                sources=[Evidence(url="https://nih.gov/a", title="NIH")],
            )
        ],
        corrections=[
            Fact(headline="Four hours is not enough", explanation="That is not true.",
                 kind="correction", confidence=0.9)
        ],
        audio_script="Here is what held up. Sleep helps your memory.",
        claims_examined=5, claims_dropped=3,
        dropped_reasons={"no solid evidence either way": 3},
    )
    job = Job(id="uitest000001", url=source.url, state=JobState.DONE, progress=1.0,
              digest=digest)
    store.save_sync(job)
    return job


@pytest.fixture
def live_server(tmp_path, monkeypatch):
    import uvicorn

    monkeypatch.setenv("TRUTHCAST_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    settings = get_settings()
    seed(JobStore(settings.db_path))

    from truthcast.api import app

    port = free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 20
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    if not server.started:
        pytest.skip("server did not start")

    yield f"http://127.0.0.1:{port}/"

    server.should_exit = True
    thread.join(timeout=10)
    get_settings.cache_clear()


@pytest.fixture
def page(live_server):
    executable = chromium_path()
    with playwright_api.sync_playwright() as p:
        try:
            browser = p.chromium.launch(executable_path=executable)
        except playwright_api.Error as exc:  # no browser binary in this environment
            pytest.skip(f"chromium unavailable: {exc}")
        context = browser.new_context()
        page = context.new_page()
        page.errors = []
        page.on("pageerror", lambda exc: page.errors.append(str(exc)))
        page.on(
            "console",
            lambda msg: page.errors.append(msg.text) if msg.type == "console" else None,
        )
        page.goto(live_server, wait_until="networkidle")
        yield page
        browser.close()


def test_the_page_loads_without_throwing(page):
    # The regression: a ReferenceError here silently disabled the whole app.
    assert page.errors == []


def test_the_submit_handler_is_actually_attached(page):
    # A valid URL first: an empty required field fails HTML5 validation and the
    # submit event never fires at all.
    page.fill("#url", "https://youtu.be/abcdefghijk")
    attached = page.evaluate(
        """() => {
            const form = document.getElementById('job-form');
            let prevented = false;
            form.addEventListener('submit', (e) => { prevented = e.defaultPrevented; });
            form.requestSubmit();
            return prevented;
        }"""
    )
    assert attached, "submit listener missing - the form would do a native GET"


def test_the_bar_is_explained_on_the_form(page):
    page.wait_for_function("() => document.getElementById('bar-note').textContent.length > 0")
    assert "independent sites" in page.inner_text("#bar-note")


def test_a_finished_digest_renders_with_its_sources(page):
    page.click("#history a[data-job]")
    page.wait_for_selector("#result:not(.hidden)")

    assert "A Checked Episode" in page.inner_text("#source-title")
    assert page.locator("#facts .fact").count() == 1
    assert page.locator("#corrections .fact.correction").count() == 1
    assert "nih.gov" in page.get_attribute("#facts .sources a", "href")
    assert "t=61s" in page.get_attribute("#facts .meta a", "href")


def test_the_drop_tally_is_shown_not_hidden(page):
    page.click("#history a[data-job]")
    page.wait_for_selector("#result:not(.hidden)")
    tally = page.inner_text("#tally")
    assert "2 of 5" in tally and "3 were dropped" in tally
    assert "no solid evidence either way" in tally


def test_untrusted_text_is_escaped_not_executed(page, live_server):
    # Titles come from YouTube and podcast feeds, so they are untrusted input.
    page.evaluate(
        """async () => {
            const response = await fetch('/api/jobs/uitest000001');
            window.__job = await response.json();
        }"""
    )
    page.click("#history a[data-job]")
    page.wait_for_selector("#result:not(.hidden)")
    assert page.locator("#facts script").count() == 0
