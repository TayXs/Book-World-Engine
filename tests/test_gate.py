"""The verification bar - the rules that decide what a listener is told."""

from conftest import make_assessment

from truthcast.models import Stance, Verdict
from truthcast.pipeline.gate import judge, partition


def test_well_evidenced_true_claim_is_kept(settings):
    decision = judge(make_assessment(verdict=Verdict.TRUE, confidence=0.92), settings)
    assert decision.keep and decision.kind == "confirmed"


def test_mostly_true_also_passes(settings):
    assert judge(make_assessment(verdict=Verdict.MOSTLY_TRUE, confidence=0.8), settings).keep


def test_low_confidence_is_dropped_even_with_many_sources(settings):
    decision = judge(
        make_assessment(confidence=0.5, domains=("a.com", "b.com", "c.com")), settings
    )
    assert not decision.keep
    assert "weak" in decision.reason


def test_single_source_is_dropped(settings):
    decision = judge(make_assessment(confidence=0.99, domains=("nih.gov",)), settings)
    assert not decision.keep
    assert "independent" in decision.reason


def test_two_pages_on_the_same_site_are_not_two_sources(settings):
    decision = judge(
        make_assessment(confidence=0.95, domains=("www.nih.gov", "news.nih.gov")), settings
    )
    assert not decision.keep, "same registered domain must not clear the independence bar"


def test_unverified_never_reaches_the_listener(settings):
    assert not judge(make_assessment(verdict=Verdict.UNVERIFIED, confidence=0.99), settings).keep


def test_false_claim_becomes_a_correction_when_enabled(settings):
    decision = judge(
        make_assessment(verdict=Verdict.FALSE, confidence=0.9, stance=Stance.REFUTES), settings
    )
    assert decision.keep and decision.kind == "correction"


def test_correction_needs_refuting_sources_not_supporting_ones(settings):
    # Evidence that supports the claim cannot justify calling it false.
    decision = judge(
        make_assessment(verdict=Verdict.FALSE, confidence=0.9, stance=Stance.SUPPORTS), settings
    )
    assert not decision.keep


def test_corrections_can_be_switched_off(settings):
    settings.include_corrections = False
    decision = judge(
        make_assessment(verdict=Verdict.MISLEADING, confidence=0.9, stance=Stance.REFUTES),
        settings,
    )
    assert not decision.keep
    assert "corrections are turned off" in decision.reason


def test_partition_tallies_why_things_were_dropped(settings):
    assessments = [
        make_assessment(claim_id="c1"),
        make_assessment(claim_id="c2", verdict=Verdict.UNVERIFIED),
        make_assessment(claim_id="c3", verdict=Verdict.UNVERIFIED),
        make_assessment(claim_id="c4", confidence=0.4),
    ]
    kept, dropped = partition(assessments, settings)
    assert [a.claim.id for a, _ in kept] == ["c1"]
    assert sum(dropped.values()) == 3
    assert dropped["no solid evidence either way"] == 2


def test_raising_the_bar_keeps_less(settings):
    assessments = [make_assessment(confidence=0.8)]
    assert len(partition(assessments, settings)[0]) == 1
    settings.min_confidence = 0.95
    assert len(partition(assessments, settings)[0]) == 0
