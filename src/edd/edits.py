"""Analyst edits, split into factual corrections and stylistic rewording.

The rate of factual corrections is the signal that matters: it says the draft was wrong. Stylistic edits are
noise for optimisation (an analyst prefers "client" to "customer") and are kept out of the quality metric.
"""

from __future__ import annotations

from edd.render import fields

FACTUAL = ("Red flags", "Risk", "Documents", "numbers")


def classify(before: str, after: str) -> str:
    if before == after:
        return "none"
    a, b = fields(before), fields(after)
    if any(a.get(k) != b.get(k) for k in FACTUAL):
        return "factual"
    return "stylistic"


def changed_fields(before: str, after: str) -> list[str]:
    a, b = fields(before), fields(after)
    return [k for k in FACTUAL if a.get(k) != b.get(k)]
