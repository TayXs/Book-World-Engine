"""Citation integrity: a verdict may only point at pages the search returned."""

from truthcast.llm import SearchHit
from truthcast.models import Stance
from truthcast.pipeline.research import EvidenceRef, format_sources, resolve_evidence

HITS = [
    SearchHit(url="https://nih.gov/a", title="NIH", snippet="from the search"),
    SearchHit(url="https://nature.com/b", title="Nature"),
]


def test_references_map_to_real_pages():
    evidence = resolve_evidence(
        [EvidenceRef(source=1, stance=Stance.SUPPORTS, what_it_says="backs it up")], HITS
    )
    assert evidence[0].url == "https://nih.gov/a"
    assert evidence[0].snippet == "backs it up"
    assert evidence[0].domain == "nih.gov"


def test_citation_to_a_source_that_does_not_exist_is_dropped():
    evidence = resolve_evidence(
        [
            EvidenceRef(source=99, stance=Stance.SUPPORTS),
            EvidenceRef(source=0, stance=Stance.SUPPORTS),
            EvidenceRef(source=2, stance=Stance.REFUTES),
        ],
        HITS,
    )
    assert [e.url for e in evidence] == ["https://nature.com/b"]


def test_the_same_page_cited_twice_counts_once():
    evidence = resolve_evidence(
        [EvidenceRef(source=1, stance=Stance.SUPPORTS)] * 3, HITS
    )
    assert len(evidence) == 1


def test_missing_snippet_falls_back_to_the_search_snippet():
    evidence = resolve_evidence([EvidenceRef(source=1, stance=Stance.SUPPORTS)], HITS)
    assert evidence[0].snippet == "from the search"


def test_sources_are_numbered_for_the_model():
    listing = format_sources(HITS)
    assert listing.startswith("1. NIH")
    assert "2. Nature" in listing
