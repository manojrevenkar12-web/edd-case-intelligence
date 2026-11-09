"""Shadow mode: a candidate configuration drafts the same live cases as production, in parallel, and nobody
sees its drafts. When the analysts' decisions on those cases are in, both are scored against them and the
candidate replaces production only if it is not worse on high-risk recall and at least as good overall."""

from __future__ import annotations

from edd.evals import Label, evaluate, paired
from edd.pipeline import Draft
from edd.settings import settings


def decide(production: list[Draft], candidate: list[Draft], decisions: dict[str, Label]) -> dict:
    cfg = settings()["shadow"]
    if len(production) < cfg["min_cases"]:
        return {"promote": False, "reason": f"only {len(production)} shadow cases; need {cfg['min_cases']}"}
    high = [d.case_id for d in production if decisions[d.case_id].risk == "high"]
    hp = [d for d in production if d.case_id in high]
    hc = [d for d in candidate if d.case_id in high]
    hr = paired(hp, hc, decisions, "risk_correct")
    cc = paired(production, candidate, decisions, "case_correct")
    ok = hr["ci"][0] > -cfg["high_risk_margin"] and cc["effect"] >= 0
    return {
        "promote": bool(ok),
        "high_risk": hr,
        "case_correct": cc,
        "production": evaluate(production, decisions),
        "candidate": evaluate(candidate, decisions),
        "reason": "non-inferior on high-risk cases and better overall" if ok else "not shown non-inferior",
    }
