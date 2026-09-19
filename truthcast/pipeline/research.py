"""Stage 2 - check each claim against the live web.

Two calls per claim, on purpose. The first lets Claude search and read freely.
The second turns those notes into a verdict that can only cite pages the search
actually returned - a model cannot invent a source it never opened.
"""

from __future__ import annotations

import asyncio
import logging

from pydantic import BaseModel, Field

from ..config import Settings
from ..llm import ClaudeClient, LLMError, ResearchResult, SearchHit
from ..models import Assessment, Claim, Evidence, MediaSource, Stance, Verdict

log = logging.getLogger(__name__)

RESEARCH_SYSTEM = """You are a fact-checker. You search the web to find out \
whether a specific claim is true.

How to work:
- Search for the claim's substance, not its wording. Try the specific numbers, \
names and dates in it.
- Go for primary sources: the study itself, the agency that publishes the \
statistic, the official record, the original announcement. A news article about \
a study is weaker than the study.
- Look for disagreement on purpose. Search for the claim being wrong, not only \
for it being right. A claim is not confirmed because the first result agrees.
- Watch the dates. A statistic that was true in 2019 may be false now, and a \
claim about "the latest" needs current data.
- Notice near-misses: right fact, wrong number; true in one country, not \
worldwide; true of a subgroup, stated about everyone. These are misleading, not \
true.
- If the evidence is thin, contested, or you cannot find real sources, say so \
plainly. "I could not verify this" is a correct and useful result.

Report what you found: what the sources say, where they disagree, how strong \
the evidence is, and what a careful person should conclude. Be concise."""

RESEARCH_PROMPT = """Check this claim, made in "{title}"{byline}.

CLAIM: {claim}

What was said: "{quote}"

Search the web and report what the evidence shows."""

VERDICT_SYSTEM = """You turn fact-checking notes into a structured verdict.

Verdicts:
- true: the evidence confirms it as stated.
- mostly_true: correct in substance, with a minor imprecision that does not \
change the point.
- misleading: the facts check out but the framing, context or scope makes a \
listener believe something false.
- false: the evidence contradicts it.
- unverified: you could not find good enough evidence either way. Use this \
freely - it is the honest answer for most thinly-sourced claims.
- not_checkable: it is opinion, prediction or too vague to test.

Confidence is about the *evidence*, not your intuition: how much would a \
careful person bet on this verdict given only the sources listed? One blog \
agreeing is not confidence. Several independent, high-quality, current sources \
agreeing is.

Cite only from the numbered sources given to you, by number. Never cite a page \
that is not on that list. If a source does not really speak to the claim, leave \
it out rather than stretching it."""

VERDICT_PROMPT = """CLAIM: {claim}

RESEARCH NOTES:
{notes}

SOURCES THE SEARCH RETURNED (cite by number):
{sources}

Give the verdict. In `real_world_link`, say in one plain sentence how this \
actually touches an ordinary person's life - what it means for their health, \
money, safety, work or what they should do differently. If it changes nothing \
for them, say that."""


class EvidenceRef(BaseModel):
    source: int = Field(description="Number of the source from the list.")
    stance: Stance = Field(description="Does this source support or refute the claim?")
    what_it_says: str = Field(default="", description="The relevant point, one line.")


class VerdictReport(BaseModel):
    verdict: Verdict
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(description="Why, in two or three sentences.")
    correction: str = Field(
        default="", description="What is actually true. Empty if the claim holds."
    )
    real_world_link: str = Field(default="")
    evidence: list[EvidenceRef] = Field(default_factory=list)


async def verify_claim(
    client: ClaudeClient, claim: Claim, source: MediaSource, settings: Settings
) -> Assessment:
    byline = f" by {source.author}" if source.author else ""

    try:
        research: ResearchResult = await client.research(
            system=RESEARCH_SYSTEM,
            user=RESEARCH_PROMPT.format(
                title=source.title, byline=byline, claim=claim.text, quote=claim.quote
            ),
            max_uses=settings.max_searches_per_claim,
        )
    except LLMError as exc:
        log.warning("research failed for %s: %s", claim.id, exc)
        return Assessment(
            claim=claim, verdict=Verdict.UNVERIFIED, rationale=f"Research failed: {exc}"
        )

    if not research.hits:
        return Assessment(
            claim=claim,
            verdict=Verdict.UNVERIFIED,
            confidence=0.0,
            rationale="No sources were found for this claim.",
        )

    try:
        report = await client.structured(
            system=VERDICT_SYSTEM,
            user=VERDICT_PROMPT.format(
                claim=claim.text,
                notes=research.text or "(no notes)",
                sources=format_sources(research.hits),
            ),
            output_model=VerdictReport,
            max_tokens=4_000,
        )
    except LLMError as exc:
        log.warning("verdict failed for %s: %s", claim.id, exc)
        return Assessment(
            claim=claim, verdict=Verdict.UNVERIFIED, rationale=f"Verdict failed: {exc}"
        )

    return Assessment(
        claim=claim,
        verdict=report.verdict,
        confidence=report.confidence,
        rationale=report.rationale.strip(),
        correction=report.correction.strip(),
        real_world_link=report.real_world_link.strip(),
        evidence=resolve_evidence(report.evidence, research.hits),
    )


async def verify_all(
    client: ClaudeClient,
    claims: list[Claim],
    source: MediaSource,
    settings: Settings,
    concurrency: int = 4,
    on_done: object | None = None,
) -> list[Assessment]:
    """Check claims in parallel; one failure never sinks the rest."""
    gate = asyncio.Semaphore(concurrency)
    finished = 0
    lock = asyncio.Lock()

    async def one(claim: Claim) -> Assessment:
        nonlocal finished
        async with gate:
            try:
                assessment = await verify_claim(client, claim, source, settings)
            except Exception as exc:  # a crash here must not lose the batch
                log.exception("verification crashed for %s", claim.id)
                assessment = Assessment(
                    claim=claim, verdict=Verdict.UNVERIFIED, rationale=f"Error: {exc}"
                )
        async with lock:
            finished += 1
            if callable(on_done):
                result = on_done(finished, len(claims), assessment)
                if hasattr(result, "__await__"):
                    await result
        return assessment

    return list(await asyncio.gather(*(one(c) for c in claims)))


def format_sources(hits: list[SearchHit]) -> str:
    lines = []
    for index, hit in enumerate(hits, start=1):
        age = f" (published {hit.published})" if hit.published else ""
        snippet = hit.snippet.replace("\n", " ").strip()
        lines.append(f"{index}. {hit.title or hit.url}{age}\n   {hit.url}\n   {snippet}")
    return "\n".join(lines)


def resolve_evidence(refs: list[EvidenceRef], hits: list[SearchHit]) -> list[Evidence]:
    """Map cited numbers back to real pages, dropping anything out of range."""
    evidence: list[Evidence] = []
    seen: set[str] = set()
    for ref in refs:
        index = ref.source - 1
        if index < 0 or index >= len(hits):
            log.warning("dropped citation to non-existent source %s", ref.source)
            continue
        hit = hits[index]
        if hit.url in seen:
            continue
        seen.add(hit.url)
        evidence.append(
            Evidence(
                url=hit.url,
                title=hit.title or hit.url,
                snippet=(ref.what_it_says or hit.snippet).strip()[:400],
                stance=ref.stance,
                published=hit.published,
            )
        )
    return evidence
