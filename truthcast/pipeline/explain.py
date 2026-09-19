"""Stage 3 - say what survived, plainly enough for a 10-year-old.

Simplifying is where a fact-checker is most likely to quietly lie: rounding a
number, dropping the caveat that made it true, turning "in the US" into
"everywhere". The prompt guards against that, and the reading-grade check runs
afterwards so "simple" stays measurable rather than assumed.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from ..config import Settings
from ..llm import ClaudeClient, LLMError
from ..models import Assessment, Digest, Fact, MediaSource, Stance, format_timestamp
from ..readability import grade_level, hard_words
from .gate import Decision

log = logging.getLogger(__name__)

WRITE_SYSTEM = """You explain verified facts to a curious 10-year-old.

How to write:
- Short sentences. One idea each.
- Everyday words. If a real word has no simple substitute (vaccine, inflation, \
algorithm), use it and explain it in the same breath.
- Concrete comparisons beat abstractions: "about as heavy as a school bus", \
"that is 3 out of every 100 people".
- Friendly and direct. Never babyish, never "wow, isn't science amazing!". \
Kids notice when they are being talked down to.

What you must not do:
- Do not add any fact that is not in the material you were given.
- Do not drop the condition that makes something true. If it is true only in \
one country, or only for adults, or only since 2023, say so - in simple words.
- Do not round a number into something different. "Almost 4 in 10" is fine for \
37%. "Half" is not.
- Do not soften a correction. If the episode said something false, say clearly \
that it is not true and what is true instead.
- Do not hedge with "experts say" - you were given the evidence; state it."""

WRITE_PROMPT = """These claims from "{title}"{byline} were checked against \
real sources. Write up each one.

For every item give:
- headline: the point in under 12 words, plain language.
- explanation: 2-4 short sentences. What is true, and how we know.
- real_world_link: one sentence on what this means for everyday life.
- relevance: 0 to 1, how much this matters to someone who cares about: {interests}

{corrections_note}
Also write `intro`: two friendly sentences telling the listener what this \
episode was about and how many things checked out.

ITEMS:
{items}"""

SIMPLIFY_SYSTEM = """You rewrite text so a 10-year-old can read it, keeping \
every fact exactly as it was. Shorter sentences, simpler words, same meaning, \
same numbers, same conditions. Never drop a qualifier to make a sentence \
shorter."""

SIMPLIFY_PROMPT = """This reads at grade {grade} - too hard. Rewrite it for \
grade {target} or below.

Hard words to replace or explain: {hard}

Keep every number and condition exactly. Return the same fields.

HEADLINE: {headline}
EXPLANATION: {explanation}
REAL WORLD: {real_world_link}"""


class WrittenFact(BaseModel):
    id: str = Field(description="The item id you were given.")
    headline: str
    explanation: str
    real_world_link: str = ""
    relevance: float = Field(default=0.5, ge=0.0, le=1.0)


class DigestDraft(BaseModel):
    intro: str
    facts: list[WrittenFact] = Field(default_factory=list)


class SimplifiedFact(BaseModel):
    headline: str
    explanation: str
    real_world_link: str = ""


async def write_digest(
    client: ClaudeClient,
    source: MediaSource,
    kept: list[tuple[Assessment, Decision]],
    settings: Settings,
    interests: list[str] | None = None,
    examined: int = 0,
    dropped: dict[str, int] | None = None,
) -> Digest:
    dropped = dropped or {}
    digest = Digest(
        source=source,
        claims_examined=examined,
        claims_dropped=sum(dropped.values()),
        dropped_reasons=dropped,
    )

    if not kept:
        digest.intro = (
            f"I checked {examined} claims from “{source.title}” and could not "
            "confirm any of them well enough to pass them on. That happens - it "
            "usually means the episode leaned on opinion, or on sources I could "
            "not find."
        )
        digest.audio_script = digest.intro
        digest.reading_grade = grade_level(digest.intro)
        return digest

    interests_text = ", ".join(interests) if interests else "general curiosity"
    corrections = [d for _, d in kept if d.kind == "correction"]
    corrections_note = (
        "Some items are corrections - the episode said something that turned out "
        "to be false. For those, lead with what is actually true.\n"
        if corrections
        else ""
    )

    try:
        draft = await client.structured(
            system=WRITE_SYSTEM,
            user=WRITE_PROMPT.format(
                title=source.title,
                byline=f" by {source.author}" if source.author else "",
                interests=interests_text,
                corrections_note=corrections_note,
                items=format_items(kept),
            ),
            output_model=DigestDraft,
        )
    except LLMError as exc:
        log.error("write-up failed: %s", exc)
        raise

    by_id = {assessment.claim.id: (assessment, decision) for assessment, decision in kept}
    facts: list[Fact] = []
    for written in draft.facts:
        pair = by_id.get(written.id)
        if pair is None:
            log.warning("model wrote up unknown item %s", written.id)
            continue
        assessment, decision = pair
        stance = Stance.REFUTES if decision.kind == "correction" else Stance.SUPPORTS
        facts.append(
            Fact(
                headline=written.headline.strip(),
                explanation=written.explanation.strip(),
                real_world_link=(written.real_world_link or assessment.real_world_link).strip(),
                kind="correction" if decision.kind == "correction" else "confirmed",
                confidence=assessment.confidence,
                said_at=format_timestamp(assessment.claim.start_seconds)
                if assessment.claim.start_seconds is not None
                else None,
                moment_url=source.at(assessment.claim.start_seconds),
                sources=[e for e in assessment.evidence if e.stance is stance],
                relevance=written.relevance,
            )
        )

    facts = await simplify_where_needed(client, facts, settings)
    facts.sort(key=lambda f: (f.relevance, f.confidence), reverse=True)

    digest.intro = draft.intro.strip()
    digest.facts = [f for f in facts if f.kind == "confirmed"]
    digest.corrections = [f for f in facts if f.kind == "correction"]
    digest.audio_script = build_script(digest)
    digest.reading_grade = grade_level(
        " ".join([digest.intro] + [f"{f.headline}. {f.explanation}" for f in facts])
    )
    return digest


async def simplify_where_needed(
    client: ClaudeClient, facts: list[Fact], settings: Settings
) -> list[Fact]:
    """Re-run anything that came back above the target reading grade."""
    target = settings.target_reading_grade

    for fact in facts:
        for _ in range(settings.max_simplify_passes):
            body = f"{fact.headline}. {fact.explanation} {fact.real_world_link}"
            grade = grade_level(body)
            fact.reading_grade = grade
            if grade <= target:
                break
            try:
                simpler = await client.structured(
                    system=SIMPLIFY_SYSTEM,
                    user=SIMPLIFY_PROMPT.format(
                        grade=grade,
                        target=target,
                        hard=", ".join(hard_words(body)[:8]) or "none",
                        headline=fact.headline,
                        explanation=fact.explanation,
                        real_world_link=fact.real_world_link,
                    ),
                    output_model=SimplifiedFact,
                    max_tokens=2_000,
                    effort="low",
                )
            except LLMError as exc:
                log.warning("simplify pass failed: %s", exc)
                break
            candidate = (
                f"{simpler.headline}. {simpler.explanation} {simpler.real_world_link}"
            )
            # Only accept a rewrite that actually reads easier.
            if grade_level(candidate) < grade:
                fact.headline = simpler.headline.strip()
                fact.explanation = simpler.explanation.strip()
                fact.real_world_link = simpler.real_world_link.strip()
                fact.reading_grade = grade_level(candidate)
            else:
                break
    return facts


def format_items(kept: list[tuple[Assessment, Decision]]) -> str:
    blocks = []
    for assessment, decision in kept:
        stance = Stance.REFUTES if decision.kind == "correction" else Stance.SUPPORTS
        evidence = [e for e in assessment.evidence if e.stance is stance]
        lines = [
            f"id: {assessment.claim.id}",
            "kind: "
            + (
                "CORRECTION - the episode was wrong"
                if decision.kind == "correction"
                else "CONFIRMED"
            ),
            f"episode said: {assessment.claim.text}",
            f"verdict: {assessment.verdict.value} (confidence {assessment.confidence:.2f})",
            f"what the evidence shows: {assessment.rationale}",
        ]
        if assessment.correction:
            lines.append(f"what is actually true: {assessment.correction}")
        if assessment.real_world_link:
            lines.append(f"why it matters: {assessment.real_world_link}")
        for evidence_item in evidence[:4]:
            lines.append(f"  source: {evidence_item.domain} - {evidence_item.snippet}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def build_script(digest: Digest) -> str:
    """A version meant for ears: no URLs, no numbering, natural pauses."""
    parts: list[str] = [digest.intro.strip()]

    if digest.facts:
        parts.append("Here is what checked out.")
        for fact in digest.facts:
            chunk = f"{fact.headline.rstrip('.')}. {fact.explanation}"
            if fact.real_world_link:
                chunk += f" {fact.real_world_link}"
            parts.append(chunk)

    if digest.corrections:
        parts.append(
            "Now the part to be careful about. "
            f"{'This claim did not' if len(digest.corrections) == 1 else 'These claims did not'} "
            "hold up."
        )
        for fact in digest.corrections:
            chunk = f"{fact.headline.rstrip('.')}. {fact.explanation}"
            if fact.real_world_link:
                chunk += f" {fact.real_world_link}"
            parts.append(chunk)

    if digest.claims_dropped:
        parts.append(
            f"I also looked at {digest.claims_dropped} other "
            f"{'claim' if digest.claims_dropped == 1 else 'claims'} and left "
            f"{'it' if digest.claims_dropped == 1 else 'them'} out, because the "
            "evidence was not strong enough."
        )

    return "\n\n".join(p for p in parts if p.strip())
