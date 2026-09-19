from truthcast.models import (
    MediaSource,
    SourceKind,
    Transcript,
    TranscriptSegment,
    format_timestamp,
    parse_timestamp,
    registered_domain,
)


def test_registered_domain_ignores_subdomains_and_www():
    assert registered_domain("https://www.nature.com/articles/x") == "nature.com"
    assert registered_domain("https://sub.deep.nasa.gov/a") == "nasa.gov"


def test_registered_domain_keeps_multipart_public_suffixes():
    # bbc.co.uk and guardian.co.uk must not both collapse to "co.uk".
    assert registered_domain("https://www.bbc.co.uk/news") == "bbc.co.uk"
    assert registered_domain("https://theguardian.co.uk/x") == "theguardian.co.uk"


def test_timestamp_round_trip():
    assert parse_timestamp("1:02:03") == 3723.0
    assert parse_timestamp("[4:05]") == 245.0
    assert parse_timestamp(90) == 90.0
    assert parse_timestamp("not a time") is None
    assert format_timestamp(3723) == "1:02:03"
    assert format_timestamp(None) == "--:--"


def test_youtube_source_links_to_the_exact_moment():
    source = MediaSource(
        kind=SourceKind.YOUTUBE, url="https://youtu.be/abcdefghijk",
        title="t", external_id="abcdefghijk",
    )
    assert source.at(61.4).endswith("watch?v=abcdefghijk&t=61s")
    assert source.at(None) is None


def test_transcript_chunks_split_on_segment_boundaries():
    segments = [TranscriptSegment(start=i * 5, end=i * 5 + 5, text="word " * 40) for i in range(20)]
    transcript = Transcript(
        source=MediaSource(kind=SourceKind.TEXT, url="x", title="t"), segments=segments
    )
    chunks = transcript.chunks(max_chars=1000)
    assert len(chunks) > 1
    assert sum(chunk.count("[") for chunk in chunks) == 20  # no segment lost or split
