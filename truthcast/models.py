"""Domain types shared by the pipeline, the API and the UI."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(UTC)


class SourceKind(StrEnum):
    YOUTUBE = "youtube"
    PODCAST = "podcast"
    AUDIO = "audio"
    TEXT = "text"


class MediaSource(BaseModel):
    kind: SourceKind
    url: str
    title: str = "Untitled"
    author: str | None = None
    published_at: str | None = None
    duration_seconds: float | None = None
    external_id: str | None = None

    def at(self, seconds: float | None) -> str | None:
        """A deep link back to the exact moment a claim was made."""
        if seconds is None:
            return None
        if self.kind is SourceKind.YOUTUBE and self.external_id:
            return f"https://www.youtube.com/watch?v={self.external_id}&t={int(seconds)}s"
        return None


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class Transcript(BaseModel):
    source: MediaSource
    segments: list[TranscriptSegment] = Field(default_factory=list)
    language: str = "en"
    origin: Literal["captions", "asr", "provided"] = "captions"

    @property
    def full_text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments if s.text.strip())

    def timestamped_text(self) -> str:
        """Transcript with [mm:ss] markers so the model can cite a moment."""
        lines = []
        for seg in self.segments:
            if not seg.text.strip():
                continue
            lines.append(f"[{format_timestamp(seg.start)}] {seg.text.strip()}")
        return "\n".join(lines)

    def chunks(self, max_chars: int = 24_000) -> list[str]:
        """Split into model-sized pieces on segment boundaries, never mid-sentence."""
        out: list[str] = []
        buf: list[str] = []
        size = 0
        for seg in self.segments:
            if not seg.text.strip():
                continue
            line = f"[{format_timestamp(seg.start)}] {seg.text.strip()}"
            if size + len(line) > max_chars and buf:
                out.append("\n".join(buf))
                buf, size = [], 0
            buf.append(line)
            size += len(line) + 1
        if buf:
            out.append("\n".join(buf))
        return out


class ClaimKind(StrEnum):
    FACTUAL = "factual"        # a statement about the world that is true or false
    STATISTICAL = "statistical"  # a number, rate, ranking or trend
    CAUSAL = "causal"          # X causes Y
    PREDICTION = "prediction"  # about the future - cannot be verified today
    OPINION = "opinion"        # taste, values, preference
    ADVICE = "advice"          # "you should ..." - checkable only via its factual premise


UNCHECKABLE_KINDS = {ClaimKind.OPINION, ClaimKind.PREDICTION}


class Claim(BaseModel):
    id: str
    text: str = Field(description="Self-contained restatement, no pronouns left dangling.")
    quote: str = Field(default="", description="What was actually said.")
    start_seconds: float | None = None
    kind: ClaimKind = ClaimKind.FACTUAL
    topic: str = ""
    importance: float = Field(default=0.5, ge=0.0, le=1.0)

    @property
    def is_checkable(self) -> bool:
        return self.kind not in UNCHECKABLE_KINDS


class Stance(StrEnum):
    SUPPORTS = "supports"
    REFUTES = "refutes"
    MIXED = "mixed"
    UNRELATED = "unrelated"


class Evidence(BaseModel):
    url: str
    title: str = ""
    snippet: str = ""
    stance: Stance = Stance.SUPPORTS
    published: str | None = None

    @property
    def domain(self) -> str:
        return registered_domain(self.url)


class Verdict(StrEnum):
    TRUE = "true"
    MOSTLY_TRUE = "mostly_true"
    MISLEADING = "misleading"
    FALSE = "false"
    UNVERIFIED = "unverified"
    NOT_CHECKABLE = "not_checkable"


PASSING_VERDICTS = {Verdict.TRUE, Verdict.MOSTLY_TRUE}
FAILING_VERDICTS = {Verdict.FALSE, Verdict.MISLEADING}


class Assessment(BaseModel):
    """What the research turned up about one claim."""

    claim: Claim
    verdict: Verdict = Verdict.UNVERIFIED
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    rationale: str = ""
    correction: str = Field(
        default="", description="What is actually true, when the claim is not."
    )
    real_world_link: str = Field(
        default="", description="How this shows up in ordinary life."
    )
    evidence: list[Evidence] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=utcnow)

    def supporting(self) -> list[Evidence]:
        return [e for e in self.evidence if e.stance is Stance.SUPPORTS]

    def refuting(self) -> list[Evidence]:
        return [e for e in self.evidence if e.stance is Stance.REFUTES]

    def independent_domains(self, stance: Stance = Stance.SUPPORTS) -> set[str]:
        return {e.domain for e in self.evidence if e.stance is stance and e.domain}


class Fact(BaseModel):
    """One verified item, written for a 10-year-old."""

    headline: str
    explanation: str
    real_world_link: str = ""
    kind: Literal["confirmed", "correction"] = "confirmed"
    confidence: float = 0.0
    reading_grade: float = 0.0
    said_at: str | None = None
    moment_url: str | None = None
    sources: list[Evidence] = Field(default_factory=list)
    relevance: float = Field(default=0.5, ge=0.0, le=1.0)


class Digest(BaseModel):
    source: MediaSource
    intro: str = ""
    facts: list[Fact] = Field(default_factory=list)
    corrections: list[Fact] = Field(default_factory=list)
    audio_script: str = ""
    reading_grade: float = 0.0
    claims_examined: int = 0
    claims_dropped: int = 0
    dropped_reasons: dict[str, int] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)


class JobState(StrEnum):
    QUEUED = "queued"
    FETCHING = "fetching"
    TRANSCRIBING = "transcribing"
    EXTRACTING = "extracting"
    RESEARCHING = "researching"
    WRITING = "writing"
    SPEAKING = "speaking"
    DONE = "done"
    FAILED = "failed"


class Job(BaseModel):
    id: str
    url: str
    state: JobState = JobState.QUEUED
    progress: float = 0.0
    message: str = ""
    interests: list[str] = Field(default_factory=list)
    digest: Digest | None = None
    audio_path: str | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class JobRequest(BaseModel):
    url: str
    interests: list[str] = Field(
        default_factory=list,
        description="Topics you care about; facts get ranked against these.",
    )
    speak: bool = False


def format_timestamp(seconds: float | None) -> str:
    if seconds is None:
        return "--:--"
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    mins, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def parse_timestamp(value: str | float | None) -> float | None:
    """Accept 83, '83', '1:23' or '1:02:03'."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    value = value.strip().strip("[]")
    if re.fullmatch(r"\d+(\.\d+)?", value):
        return float(value)
    parts = value.split(":")
    if not all(re.fullmatch(r"\d+(\.\d+)?", p) for p in parts):
        return None
    total = 0.0
    for part in parts:
        total = total * 60 + float(part)
    return total


_PUBLIC_SUFFIXES = {
    "co.uk", "ac.uk", "gov.uk", "org.uk", "com.au", "edu.au", "gov.au",
    "co.jp", "co.nz", "co.za", "com.br", "org.nz", "ac.nz",
}


def registered_domain(url: str) -> str:
    """Host minus subdomains - two sites on the same domain are not independent."""
    match = re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://([^/?#]+)", url.strip())
    host = (match.group(1) if match else url.strip().split("/")[0]).lower()
    host = host.split("@")[-1].split(":")[0]
    host = host.removeprefix("www.")
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    last_two = ".".join(parts[-2:])
    if last_two in _PUBLIC_SUFFIXES:
        return ".".join(parts[-3:])
    return last_two
