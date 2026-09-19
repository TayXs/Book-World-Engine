"""Response parsing - especially the shapes that do not raise."""

import pytest

from truthcast.llm import ClaudeClient, RefusalError, dedupe_hits, harvest_blocks


def test_harvest_collects_search_results_and_counts_searches():
    text, hits, searches = harvest_blocks(
        [
            {"type": "text", "text": "Here is what I found."},
            {
                "type": "web_search_tool_result",
                "content": [
                    {"url": "https://nih.gov/a", "title": "NIH", "snippet": "sleep"},
                    {"url": "https://nature.com/b", "title": "Nature"},
                ],
            },
        ]
    )
    assert text == "Here is what I found."
    assert [h.url for h in hits] == ["https://nih.gov/a", "https://nature.com/b"]
    assert searches == 1


def test_failed_search_returns_an_error_object_not_a_list():
    # The API reports server-tool failures with HTTP 200 and an error object,
    # so indexing content blindly would crash the run.
    text, hits, searches = harvest_blocks(
        [{"type": "web_search_tool_result", "content": {"error_code": "max_uses_exceeded"}}]
    )
    assert hits == [] and searches == 1 and text == ""


def test_citations_on_text_blocks_are_captured():
    _, hits, _ = harvest_blocks(
        [
            {
                "type": "text",
                "text": "Sleep matters.",
                "citations": [
                    {"url": "https://cdc.gov/sleep", "title": "CDC", "cited_text": "7+ hours"}
                ],
            }
        ]
    )
    assert hits[0].url == "https://cdc.gov/sleep"
    assert hits[0].snippet == "7+ hours"


def test_dedupe_keeps_one_entry_per_url_and_fills_in_the_snippet():
    from truthcast.llm import SearchHit

    hits = dedupe_hits(
        [
            SearchHit(url="https://a.com/x", title="A"),
            SearchHit(url="https://a.com/x", title="A", snippet="the detail"),
            SearchHit(url="https://b.com/y"),
        ]
    )
    assert len(hits) == 2
    assert hits[0].snippet == "the detail"


def test_thinking_blocks_are_ignored():
    text, hits, _ = harvest_blocks([{"type": "thinking", "thinking": ""}])
    assert text == "" and hits == []


def test_refusal_stop_reason_raises(settings):
    class Response:
        stop_reason = "refusal"
        stop_details = type("D", (), {"category": "cyber"})()

    from truthcast.llm import _guard_stop_reason

    with pytest.raises(RefusalError, match="cyber"):
        _guard_stop_reason(Response())


def test_client_construction_does_not_need_credentials(settings):
    # Building the client must not reach out - only using it should.
    ClaudeClient(settings)
