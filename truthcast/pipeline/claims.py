"""Stage 1 - pull the checkable assertions out of a transcript.

A long episode is mostly banter. What matters is the handful of statements that
are presented as fact and would change what a listener believes.
"""

from __future__ import annotations

import asyncio
import logging
import re

from pydantic import BaseModel, Field

from ..config import Settings
from ..llm import ClaudeClient, LLMError
from ..models import Claim, ClaimKind, Transcript, parse_timestamp

log = logging.getLogger(__name__)

SYSTEM = """You extract checkable claims from spoken transcripts.

A claim qualifies when it is stated as fact about the world and a careful \
researcher could confirm or disprove it with public evidence: numbers, \
historical events, scientific findings, what a named person or organisation \
did or said, how something works, cause-and-effect assertions.

Skip: small talk, jokes, hypotheticals, sponsor reads, personal anecdotes that \
nobody could check, and vague gestures like "studies show" with no substance.

Rules that matter:
- Rewrite each claim so it stands alone. Resolve every "he", "they", "this" and \
"that year" into the actual name, number or date. A researcher will read your \
claim with no access to the transcript.
- Quote what was actually said, briefly and verbatim.
- Keep the speaker's meaning. Do not make a claim more reasonable, more extreme, \
or more precise than it was.
- Tag the kind honestly. A forecast about the future is a prediction, not a fact. \
A value judgement is an opinion.
- importance: how much it would matter if a listener believed this and it were \
false. Health, money, safety and civic claims run high; trivia runs low."""

INSTRUCTION = """Transcript of "{title}"{byline}, part {index} of {total}.
Each line starts with the timestamp where it was said.

Pull out every checkable claim, at most {limit} from this part. If this part \
contains nothing checkable, return an empty list.

For `said_at`, copy the timestamp of the line the claim came from.

---
{chunk}"""


class ClaimDraft(BaseModel):
    text: str = Field(description="The claim, self-contained, one sentence.")
    quote: str = Field(description="What the speaker actually said, verbatim.")
    said_at: str = Field(default="", description="Timestamp from the line, e.g. 12:04")
    kind: ClaimKind = ClaimKind.FACTUAL
    topic: str = Field(default="", description="Two or three words.")
    importance: float = Field(default=0.5, ge=0.0, le=1.0)


class ClaimBatch(BaseModel):
    claims: list[ClaimDraft] = Field(default_factory=list)


async def extract_claims(
    client: ClaudeClient,
    transcript: Transcript,
    settings: Settings,
    concurrency: int = 4,
) -> list[Claim]:
    """Extract from each chunk in parallel, then merge, dedupe and rank."""
    chunks = transcript.chunks()
    if not chunks:
        return []

    per_chunk = max(3, -(-settings.max_claims // len(chunks)) + 2)
    byline = f" by {transcript.source.author}" if transcript.source.author else ""
    gate = asyncio.Semaphore(concurrency)

    async def one(index: int, chunk: str) -> list[ClaimDraft]:
        async with gate:
            try:
                batch = await client.structured(
                    system=SYSTEM,
                    user=INSTRUCTION.format(
                        title=transcript.source.title,
                        byline=byline,
                        index=index + 1,
                        total=len(chunks),
                        limit=per_chunk,
                        chunk=chunk,
                    ),
                    output_model=ClaimBatch,
                    model=settings.extraction_model,
                    effort="medium",
                )
                return batch.claims
            except LLMError as exc:
                # One bad chunk should not cost the whole episode.
                log.warning("claim extraction failed for chunk %s: %s", index + 1, exc)
                return []

    results = await asyncio.gather(*(one(i, c) for i, c in enumerate(chunks)))
    drafts = [draft for group in results for draft in group]
    return rank_and_dedupe(drafts, settings.max_claims)


def rank_and_dedupe(drafts: list[ClaimDraft], limit: int) -> list[Claim]:
    """Checkable claims only, most consequential first, no near-duplicates."""
    claims: list[Claim] = []
    fingerprints: list[set[str]] = []

    ordered = sorted(drafts, key=lambda d: d.importance, reverse=True)
    for draft in ordered:
        text = draft.text.strip()
        if not text:
            continue
        claim = Claim(
            id=f"c{len(claims) + 1}",
            text=text,
            quote=draft.quote.strip(),
            start_seconds=parse_timestamp(draft.said_at),
            kind=draft.kind,
            topic=draft.topic.strip(),
            importance=draft.importance,
        )
        if not claim.is_checkable:
            continue
        fingerprint = _fingerprint(text)
        if any(_overlap(fingerprint, seen) >= 0.8 for seen in fingerprints):
            continue
        fingerprints.append(fingerprint)
        claims.append(claim)
        if len(claims) >= limit:
            break

    # Renumber so ids stay dense after filtering.
    for position, claim in enumerate(claims, start=1):
        claim.id = f"c{position}"
    return claims


_STOPWORDS = {
    "the", "a", "an", "of", "in", "to", "is", "are", "was", "were", "and", "or",
    "that", "this", "it", "on", "for", "by", "with", "as", "at", "from", "has",
    "have", "had", "be", "been", "will", "than", "then", "more", "most",
}


def _fingerprint(text: str) -> set[str]:
    """Content words, lightly stemmed, plus every number.

    Numbers are kept whatever their length: "prices rose 30%" and "prices rose
    50%" are different claims and must never be merged as duplicates.
    """
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    out: set[str] = set()
    for token in tokens:
        if token.isdigit():
            out.add(token)
        elif token not in _STOPWORDS and len(token) > 2:
            out.add(_stem(token))
    return out


def _stem(word: str) -> str:
    """Crude suffix strip so "produces" and "produced" look alike."""
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def _overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)
