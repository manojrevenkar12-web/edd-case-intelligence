"""Inter-annotator agreement on the golden set, and adjudication.

Two EDD subject-matter experts label the same cases with the taxonomy. Where they agree, that is the label.
Where they disagree, a senior reviewer adjudicates against the written guideline. Cohen's kappa per flag shows
which definitions the guideline still leaves open; those go back to the SMEs before the set is used.
"""

from __future__ import annotations

from dataclasses import dataclass

from edd.taxonomy import flag_names


def cohen_kappa(a: list, b: list) -> float:
    n = len(a)
    cats = sorted(set(a) | set(b))
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


@dataclass
class Annotation:
    case_id: str
    annotator: str
    flags: set[str]
    risk: str


def agreement(a: list[Annotation], b: list[Annotation]) -> dict:
    by_b = {x.case_id: x for x in b}
    pairs = [(x, by_b[x.case_id]) for x in a if x.case_id in by_b]
    out = {"cases": len(pairs), "flags": {}}
    for f in flag_names():
        out["flags"][f] = cohen_kappa([f in x.flags for x, _ in pairs], [f in y.flags for _, y in pairs])
    out["risk"] = cohen_kappa([x.risk for x, _ in pairs], [y.risk for _, y in pairs])
    out["disagreements"] = sum(x.flags != y.flags or x.risk != y.risk for x, y in pairs)
    return out


def adjudicate(a: list[Annotation], b: list[Annotation], senior: dict[str, Annotation]) -> dict[str, Annotation]:
    """Agreement stands; any disagreement takes the senior reviewer's label."""
    by_b = {x.case_id: x for x in b}
    out = {}
    for x in a:
        y = by_b[x.case_id]
        out[x.case_id] = x if (x.flags == y.flags and x.risk == y.risk) else senior[x.case_id]
    return out
