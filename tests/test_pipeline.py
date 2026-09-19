"""End-to-end run of everything after the transcript, with Claude stubbed out."""

from __future__ import annotations

import re

import pytest

from truthcast.llm import ClaudeClient, ResearchResult, SearchHit
from truthcast.models import (
    MediaSource,
    Stance,
    Transcript,
    TranscriptSegment,
    Verdict,
)
from truthcast.pipeline.claims import ClaimBatch, ClaimDraft
from truthcast.pipeline.digest import build_digest
from truthcast.pipeline.explain import DigestDraft, SimplifiedFact, WrittenFact, build_script
from truthcast.pipeline.research import EvidenceRef, VerdictReport

SIMPLE = "Adults sleep about seven hours. That is less than ten years ago."
DENSE = (
    "Epidemiological investigations demonstrate that insufficient somnolence "
    "precipitates deleterious cardiovascular sequelae among adult populations."
)


class FakeClaude(ClaudeClient):
    """Answers each stage with a canned object, and records what it was asked."""

    def __init__(self, settings, verdicts=None, hits=None, headline_text=SIMPLE):
        super().__init__(settings, client=object())
        self.verdicts = verdicts or {}
        self.hits = hits if hits is not None else [
            SearchHit(url="https://nih.gov/a", title="NIH"),
            SearchHit(url="https://nature.com/b", title="Nature"),
        ]
        self.headline_text = headline_text
        self.calls: list[str] = []
        self.researched: list[str] = []

    async def research(self, *, system, user, max_uses=None, max_tokens=8000):
        self.calls.append("research")
        self.researched.append(user)
        return ResearchResult(text="notes", hits=list(self.hits), searches=1)

    async def structured(self, *, system, user, output_model, **kwargs):
        self.calls.append(output_model.__name__)

        if output_model is ClaimBatch:
            return ClaimBatch(
                claims=[
                    ClaimDraft(
                        text="Adults need seven to nine hours of sleep.",
                        quote="you need seven to nine hours",
                        said_at="1:01",
                        importance=0.9,
                    ),
                    ClaimDraft(
                        text="Sleeping four hours is enough for most people.",
                        quote="four hours is plenty",
                        said_at="2:30",
                        importance=0.8,
                    ),
                    ClaimDraft(
                        text="Naps cure every illness.",
                        quote="naps cure everything",
                        said_at="3:30",
                        importance=0.7,
                    ),
                ]
            )

        if output_model is VerdictReport:
            for text, report in self.verdicts.items():
                if text in user:
                    return report
            return VerdictReport(
                verdict=Verdict.UNVERIFIED, confidence=0.1, rationale="nothing found"
            )

        if output_model is DigestDraft:
            ids = re.findall(r"^id: (\S+)$", user, flags=re.MULTILINE)
            return DigestDraft(
                intro="Here is what held up.",
                facts=[
                    WrittenFact(
                        id=claim_id,
                        headline="Sleep is worth it",
                        explanation=self.headline_text,
                        real_world_link="Go to bed earlier.",
                        relevance=0.9 - index * 0.1,
                    )
                    for index, claim_id in enumerate(ids)
                ],
            )

        if output_model is SimplifiedFact:
            return SimplifiedFact(
                headline="Sleep is worth it",
                explanation=SIMPLE,
                real_world_link="Go to bed earlier.",
            )

        raise AssertionError(f"unexpected model {output_model}")


def transcript(source: MediaSource) -> Transcript:
    return Transcript(
        source=source,
        segments=[
            TranscriptSegment(start=61, end=70, text="You need seven to nine hours."),
            TranscriptSegment(start=150, end=160, text="Four hours is plenty, honestly."),
            TranscriptSegment(start=210, end=220, text="Naps cure everything."),
        ],
    )


def supported(confidence=0.9):
    return VerdictReport(
        verdict=Verdict.TRUE,
        confidence=confidence,
        rationale="Both sources agree.",
        real_world_link="Sleep more.",
        evidence=[
            EvidenceRef(source=1, stance=Stance.SUPPORTS),
            EvidenceRef(source=2, stance=Stance.SUPPORTS),
        ],
    )


def refuted():
    return VerdictReport(
        verdict=Verdict.FALSE,
        confidence=0.93,
        rationale="Both sources contradict it.",
        correction="Most adults need far more than four hours.",
        evidence=[
            EvidenceRef(source=1, stance=Stance.REFUTES),
            EvidenceRef(source=2, stance=Stance.REFUTES),
        ],
    )


@pytest.mark.asyncio
async def test_verified_claims_survive_and_unverified_ones_do_not(settings, source):
    client = FakeClaude(
        settings,
        verdicts={
            "seven to nine hours": supported(),
            "four hours is enough": refuted(),
            # "Naps cure every illness" falls through to UNVERIFIED.
        },
    )
    digest = await build_digest(transcript(source), client=client, settings=settings)

    assert digest.claims_examined == 3
    assert len(digest.facts) == 1
    assert len(digest.corrections) == 1
    assert digest.claims_dropped == 1
    assert digest.dropped_reasons == {"no solid evidence either way": 1}


@pytest.mark.asyncio
async def test_every_claim_gets_its_own_research_call(settings, source):
    client = FakeClaude(settings, verdicts={"seven to nine hours": supported()})
    await build_digest(transcript(source), client=client, settings=settings)
    assert client.calls.count("research") == 3


@pytest.mark.asyncio
async def test_a_claim_backed_by_one_site_is_withheld(settings, source):
    client = FakeClaude(
        settings,
        hits=[SearchHit(url="https://nih.gov/a"), SearchHit(url="https://www.nih.gov/b")],
        verdicts={"seven to nine hours": supported()},
    )
    digest = await build_digest(transcript(source), client=client, settings=settings)
    assert digest.facts == []
    assert "independent" in "".join(digest.dropped_reasons)


@pytest.mark.asyncio
async def test_facts_carry_sources_and_a_link_back_to_the_moment(settings, source):
    client = FakeClaude(settings, verdicts={"seven to nine hours": supported()})
    digest = await build_digest(transcript(source), client=client, settings=settings)
    fact = digest.facts[0]
    assert fact.said_at == "1:01"
    assert fact.moment_url.endswith("&t=61s")
    assert {s.domain for s in fact.sources} == {"nih.gov", "nature.com"}


@pytest.mark.asyncio
async def test_hard_writing_is_sent_back_to_be_simplified(settings, source):
    client = FakeClaude(
        settings, verdicts={"seven to nine hours": supported()}, headline_text=DENSE
    )
    digest = await build_digest(transcript(source), client=client, settings=settings)
    assert "SimplifiedFact" in client.calls
    assert digest.facts[0].reading_grade <= settings.target_reading_grade


@pytest.mark.asyncio
async def test_easy_writing_is_left_alone(settings, source):
    client = FakeClaude(settings, verdicts={"seven to nine hours": supported()})
    await build_digest(transcript(source), client=client, settings=settings)
    assert "SimplifiedFact" not in client.calls


@pytest.mark.asyncio
async def test_nothing_verified_still_produces_an_honest_digest(settings, source):
    client = FakeClaude(settings, verdicts={})
    digest = await build_digest(transcript(source), client=client, settings=settings)
    assert digest.facts == [] and digest.corrections == []
    assert "could not confirm" in digest.intro
    assert digest.audio_script


@pytest.mark.asyncio
async def test_progress_is_reported_through_the_stages(settings, source):
    seen: list[tuple[str, float]] = []

    async def on_progress(state, message, pct):
        seen.append((state.value, pct))

    client = FakeClaude(settings, verdicts={"seven to nine hours": supported()})
    await build_digest(
        transcript(source), client=client, settings=settings, on_progress=on_progress
    )
    states = [s for s, _ in seen]
    assert "extracting" in states and "researching" in states and "writing" in states
    assert seen == sorted(seen, key=lambda item: item[1])  # never goes backwards


def test_the_audio_script_reads_aloud_without_urls(settings, source):
    from truthcast.models import Digest, Fact

    digest = Digest(
        source=source,
        intro="Here is what held up.",
        facts=[Fact(headline="Sleep is worth it", explanation=SIMPLE,
                    real_world_link="Go to bed earlier.")],
        corrections=[Fact(headline="Four hours is not enough", explanation="It is not true.",
                          kind="correction")],
        claims_dropped=2,
    )
    script = build_script(digest)
    assert "http" not in script
    assert "Here is what checked out." in script
    assert "did not" in script and "2 other claims" in script
