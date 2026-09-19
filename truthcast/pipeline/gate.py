"""The bar a claim has to clear to reach you.

This is the whole point of the app: what gets *dropped* matters more than what
gets written. Everything here is deliberately mechanical - the model proposes a
verdict, but these rules decide what you are told.
"""

from __future__ import annotations

from typing import Literal, NamedTuple

from ..config import Settings
from ..models import (
    FAILING_VERDICTS,
    PASSING_VERDICTS,
    Assessment,
    Stance,
    Verdict,
)


class Decision(NamedTuple):
    keep: bool
    kind: Literal["confirmed", "correction", "dropped"]
    reason: str


REASONS = {
    "not_checkable": "not something evidence can settle",
    "unverified": "no solid evidence either way",
    "low_confidence": "evidence too weak to be sure",
    "single_source": "only one source - needs independent backing",
    "corrections_off": "disproven, and corrections are turned off",
}


def judge(assessment: Assessment, settings: Settings) -> Decision:
    verdict = assessment.verdict

    if verdict is Verdict.NOT_CHECKABLE or not assessment.claim.is_checkable:
        return Decision(False, "dropped", REASONS["not_checkable"])

    if verdict is Verdict.UNVERIFIED:
        return Decision(False, "dropped", REASONS["unverified"])

    if assessment.confidence < settings.min_confidence:
        return Decision(False, "dropped", REASONS["low_confidence"])

    if verdict in PASSING_VERDICTS:
        stance = Stance.SUPPORTS
        kind: Literal["confirmed", "correction"] = "confirmed"
    elif verdict in FAILING_VERDICTS:
        if not settings.include_corrections:
            return Decision(False, "dropped", REASONS["corrections_off"])
        stance = Stance.REFUTES
        kind = "correction"
    else:  # pragma: no cover - every verdict is covered above
        return Decision(False, "dropped", REASONS["unverified"])

    if len(assessment.independent_domains(stance)) < settings.min_independent_sources:
        return Decision(False, "dropped", REASONS["single_source"])

    return Decision(True, kind, "verified")


def partition(
    assessments: list[Assessment], settings: Settings
) -> tuple[list[tuple[Assessment, Decision]], dict[str, int]]:
    """Split into what survived and a tally of why the rest did not."""
    kept: list[tuple[Assessment, Decision]] = []
    dropped: dict[str, int] = {}
    for assessment in assessments:
        decision = judge(assessment, settings)
        if decision.keep:
            kept.append((assessment, decision))
        else:
            dropped[decision.reason] = dropped.get(decision.reason, 0) + 1
    return kept, dropped
