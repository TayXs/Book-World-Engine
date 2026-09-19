from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthcast.config import Settings
from truthcast.models import (
    Assessment,
    Claim,
    Evidence,
    MediaSource,
    SourceKind,
    Stance,
    Verdict,
)


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        data_dir=tmp_path,
        min_confidence=0.75,
        min_independent_sources=2,
        include_corrections=True,
        target_reading_grade=5.0,
    )


@pytest.fixture
def source() -> MediaSource:
    return MediaSource(
        kind=SourceKind.YOUTUBE,
        url="https://www.youtube.com/watch?v=abcdefghijk",
        title="Everything You Know About Sleep Is Wrong",
        author="Deep Dive Pod",
        external_id="abcdefghijk",
    )


def make_assessment(
    *,
    verdict: Verdict = Verdict.TRUE,
    confidence: float = 0.9,
    domains: tuple[str, ...] = ("nih.gov", "nature.com"),
    stance: Stance = Stance.SUPPORTS,
    claim_id: str = "c1",
) -> Assessment:
    return Assessment(
        claim=Claim(id=claim_id, text="Adults need seven to nine hours of sleep.", quote="q",
                    start_seconds=61.0),
        verdict=verdict,
        confidence=confidence,
        rationale="Because the sources say so.",
        evidence=[
            Evidence(url=f"https://{d}/page", title=d, snippet="evidence", stance=stance)
            for d in domains
        ],
    )


@pytest.fixture
def assessment_factory():
    return make_assessment
