"""Reading-level scoring, so 'a 10-year-old can understand it' is measurable.

Flesch-Kincaid grade level: roughly the US school grade needed to read a text.
A 10-year-old is in grade 4-5, so the pipeline aims at 5.0 and rewrites anything
that comes back harder than that.
"""

from __future__ import annotations

import re

_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")  # noqa: RUF001 - curly apostrophes are real input
_SENTENCE_END = re.compile(r"[.!?]+(?=\s|$)")
_VOWEL_GROUP = re.compile(r"[aeiouy]+")

# Suffixes that add a syllable the vowel-group rule misses.
_SYLLABLE_ADDERS = ("ia", "io", "ua", "uo", "eo", "ism", "ual")


def count_syllables(word: str) -> int:
    word = word.lower().strip("'’-")  # noqa: RUF001 - curly apostrophes are real input
    if not word:
        return 0
    groups = len(_VOWEL_GROUP.findall(word))
    # Silent terminal 'e' ("make" is one syllable, "the" stays one).
    if word.endswith("e") and not word.endswith(("le", "ee", "ye")) and groups > 1:
        groups -= 1
    for adder in _SYLLABLE_ADDERS:
        if adder in word:
            groups += 1
            break
    return max(1, groups)


def count_words(text: str) -> int:
    return len(_WORD.findall(text))


def count_sentences(text: str) -> int:
    text = text.strip()
    if not text:
        return 0
    # Line breaks end a thought too - headlines and bullets rarely take a period.
    lines = [line for line in text.splitlines() if line.strip()]
    total = sum(len(_SENTENCE_END.findall(line)) or 1 for line in lines)
    return max(1, total)


def grade_level(text: str) -> float:
    """Flesch-Kincaid grade level, floored at 0."""
    words = _WORD.findall(text)
    if not words:
        return 0.0
    sentences = count_sentences(text)
    syllables = sum(count_syllables(w) for w in words)
    score = (
        0.39 * (len(words) / sentences) + 11.8 * (syllables / len(words)) - 15.59
    )
    return max(0.0, round(score, 2))


def hard_words(text: str, min_syllables: int = 4) -> list[str]:
    """The words most likely to be why a passage scored badly."""
    seen: dict[str, None] = {}
    for word in _WORD.findall(text):
        if count_syllables(word) >= min_syllables and word.lower() not in seen:
            seen[word.lower()] = None
    return list(seen)
