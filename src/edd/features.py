"""Deterministic facts and indicators computed from a case, and the checks a model's claims must pass.

Five of the seven red flags in the taxonomy are arithmetic over transfers; code computes them exactly, with the
transfer ids that show them. The other two (profile mismatch, crypto off-ramp) need reading: what the customer
declared, which counterparty is an exchange. Those are the model's to propose and the analyst's to confirm.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from edd.schema import CaseRecord, TransferRecord
from edd.taxonomy import taxonomy

COMPUTED = ["structuring", "pass_through", "high_velocity_inbound", "funnel_outbound", "high_risk_jurisdiction"]
JUDGEMENT = ["profile_mismatch", "crypto_offramp"]


@dataclass
class Indicator:
    flag: str
    evidence: list[str]


def facts(case: CaseRecord) -> dict:
    ins = [t for t in case.transfers if t.direction == "in"]
    outs = [t for t in case.transfers if t.direction == "out"]
    by_cp: dict[str, float] = defaultdict(float)
    for t in case.transfers:
        by_cp[t.counterparty] += t.amount_eur
    return {
        "total_in_eur": round(sum(t.amount_eur for t in ins), 2),
        "total_out_eur": round(sum(t.amount_eur for t in outs), 2),
        "transfers": len(case.transfers),
        "largest_counterparty": max(by_cp, key=by_cp.get) if by_cp else "",
    }


def indicators(case: CaseRecord) -> list[Indicator]:
    t = taxonomy()
    thr = t["reporting_threshold_eur"]
    ins = sorted((x for x in case.transfers if x.direction == "in"), key=lambda x: x.hour)
    outs = [x for x in case.transfers if x.direction == "out"]
    found: list[Indicator] = []

    near = [x for x in ins if 0.9 * thr <= x.amount_eur < thr]
    for i in range(len(near) - 2):
        if near[i + 2].hour - near[i].hour <= 30 * 24:
            found.append(Indicator("structuring", [x.id for x in near[i : i + 3]]))
            break

    pairs: list[str] = []
    for i in (x for x in ins if x.amount_eur > 500):
        o = next(
            (o for o in outs if 0 < o.hour - i.hour <= 48 and 0.8 * i.amount_eur <= o.amount_eur <= i.amount_eur), None
        )
        if o is not None:
            pairs += [i.id, o.id]
    if len(pairs) >= 4:
        found.append(Indicator("pass_through", pairs[:6]))

    for i, first in enumerate(ins):
        window = [x for x in ins[i:] if x.hour - first.hour <= 14 * 24]
        if len(window) >= 20 and len({x.counterparty for x in window}) >= 15:
            found.append(Indicator("high_velocity_inbound", [x.id for x in window[:20]]))
            break

    out_value = sum(x.amount_eur for x in outs)
    by_cp: dict[str, list[TransferRecord]] = defaultdict(list)
    for x in outs:
        if x.country != case.country:
            by_cp[x.counterparty].append(x)
    if out_value and by_cp:
        _, txs = max(by_cp.items(), key=lambda kv: sum(x.amount_eur for x in kv[1]))
        if sum(x.amount_eur for x in txs) / out_value >= 0.7:
            found.append(Indicator("funnel_outbound", [x.id for x in txs[:5]]))

    hrj = [x.id for x in case.transfers if x.country in t["high_risk_jurisdictions"]]
    if hrj:
        found.append(Indicator("high_risk_jurisdiction", hrj[:5]))
    return found


def evidence_holds(case: CaseRecord, flag: str, evidence: list[str]) -> bool:
    """Does the cited evidence exist, and does it show the kind of activity the flag describes?"""
    t = taxonomy()
    by_id = {x.id: x for x in case.transfers}
    cited = [by_id[e] for e in evidence if e in by_id]
    if not cited or len(cited) < len(evidence):
        return False
    thr = t["reporting_threshold_eur"]
    if flag == "structuring":
        return len(cited) >= 3 and all(x.direction == "in" and 0.9 * thr <= x.amount_eur < thr for x in cited)
    if flag == "pass_through":
        ins = [x for x in cited if x.direction == "in"]
        outs = [x for x in cited if x.direction == "out"]
        return any(0 < o.hour - i.hour <= 48 and o.amount_eur >= 0.8 * i.amount_eur for i in ins for o in outs)
    if flag == "high_velocity_inbound":
        return all(x.direction == "in" for x in cited) and len({x.counterparty for x in cited}) >= 5
    if flag == "funnel_outbound":
        return all(x.direction == "out" for x in cited) and len({x.counterparty for x in cited}) == 1
    if flag == "high_risk_jurisdiction":
        return all(x.country in t["high_risk_jurisdictions"] for x in cited)
    if flag == "crypto_offramp":
        return all(x.direction == "out" for x in cited)
    return flag in t["flags"]
