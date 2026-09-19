"""The stages: pull out claims, check them, keep what survives, explain it."""

from .claims import extract_claims
from .digest import build_digest, run
from .explain import write_digest
from .research import verify_all, verify_claim

__all__ = [
    "build_digest",
    "extract_claims",
    "run",
    "verify_all",
    "verify_claim",
    "write_digest",
]
