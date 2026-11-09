"""The people around the workbench (truth side): two EDD SMEs and a senior reviewer who label the golden set,
and the analysts who review drafts in production and edit them."""

from __future__ import annotations

import hashlib

from edd.agreement import Annotation
from edd.render import render_final
from edd_world.cases import Case
from edd_world.truth import TAXONOMY

FLAGS = list(TAXONOMY["flags"])
LEVELS = ["low", "medium", "high"]


def _u(*parts: object) -> float:
    return int.from_bytes(hashlib.blake2b("|".join(map(str, parts)).encode(), digest_size=8).digest(), "big") / 2**64


def annotate(c: Case, who: str) -> Annotation:
    """SME A reads 'profile mismatch' broadly; SME B narrowly and sometimes misses a pass-through."""
    flags = set(c.truth_flags)
    risk = c.truth_risk
    if who == "sme_a":
        if (
            "profile_mismatch" not in flags
            and c.typology in ("freelancer", "marketplace_seller")
            and _u(c.id, who, 1) < 0.25
        ):
            flags.add("profile_mismatch")
        if _u(c.id, who, 2) < 0.03:
            risk = LEVELS[min(2, LEVELS.index(risk) + 1)]
    elif who == "sme_b":
        if "profile_mismatch" in flags and _u(c.id, who, 1) < 0.22:
            flags.discard("profile_mismatch")
        if "pass_through" in flags and _u(c.id, who, 3) < 0.08:
            flags.discard("pass_through")
        if _u(c.id, who, 2) < 0.06:
            risk = LEVELS[max(0, LEVELS.index(risk) - 1)]
    elif who == "senior" and _u(c.id, who, 4) < 0.01:
        risk = LEVELS[(LEVELS.index(risk) + 1) % 3]
    return Annotation(c.id, who, flags, risk)


STYLE = [
    ("Received", "Got"),
    ("sent", "paid out"),
    ("customer", "client"),
    ("largest counterparty", "main counterparty"),
]


def analyst_review(c: Case, draft_text: str) -> tuple[str, dict]:
    """The analyst's final version of a draft and their decision. They fix what is wrong and sometimes reword."""
    decision = {"flags": sorted(c.truth_flags), "risk": c.truth_risk, "documents": sorted(c.truth_documents)}
    final = render_final(draft_text, decision)
    if _u(c.id, "style") < 0.35:
        a, b = STYLE[int(_u(c.id, "which") * len(STYLE))]
        final = final.replace(a, b, 1)
    return final, decision
