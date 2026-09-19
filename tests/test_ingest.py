import pytest

from truthcast.ingest import classify, podcast, youtube
from truthcast.ingest.errors import IngestError, TranscriptUnavailable
from truthcast.models import SourceKind


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ?t=42", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/watch?list=PL1&v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/live/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://example.com/episode.mp3", None),
        ("https://vimeo.com/12345", None),
    ],
)
def test_youtube_ids_are_found_in_every_link_shape(url, expected):
    assert youtube.video_id(url) == expected


def test_sources_are_routed_to_the_right_ingester():
    assert classify("https://youtu.be/dQw4w9WgXcQ") is SourceKind.YOUTUBE
    assert classify("https://cdn.example.com/ep12.mp3?token=x") is SourceKind.AUDIO
    assert classify("https://feeds.megaphone.fm/show") is SourceKind.PODCAST


def test_audio_is_recognised_by_extension_not_by_query_string():
    assert podcast.looks_like_audio("https://x.com/a.m4a?sig=abc")
    assert not podcast.looks_like_audio("https://x.com/feed?format=mp3")


@pytest.mark.asyncio
async def test_a_non_youtube_link_is_refused_by_the_youtube_ingester():
    with pytest.raises(IngestError):
        await youtube.fetch_metadata("https://example.com/not-a-video")


def test_missing_captions_is_a_recoverable_failure():
    # It must be catchable as the specific "try the audio instead" signal.
    assert issubclass(TranscriptUnavailable, IngestError)
