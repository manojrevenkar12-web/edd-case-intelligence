"""What an experienced EDD reviewer would conclude about a case, given everything (truth side)."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import yaml

from edd_world.cases import EXCHANGES, NEW_EXCHANGES, Case

TAXONOMY = yaml.safe_load((Path(__file__).resolve().parents[2] / "config" / "taxonomy.yaml").read_text())
MITIGATING_DECLARATION = {
    "online marketplace seller": "marketplace_seller",
    "payroll services": "payroll_provider",
    "warehouse worker": "remittance_family",
}
# Occupations a reviewer reads as inconsistent with running other people's money.
LOW_VOLUME_OCCUPATIONS = {"student", "retail assistant", "nurse", "warehouse worker"}


def _flags(c: Case) -> set[str]:
    t = TAXONOMY
    thr = t["reporting_threshold_eur"]
    ins = [x for x in c.transfers if x.direction == "in"]
    outs = [x for x in c.transfers if x.direction == "out"]
    flags: set[str] = set()
    near = sorted(x.hour for x in ins if 0.9 * thr <= x.amount_eur < thr)
    if any(near[i + 2] - near[i] <= 30 * 24 for i in range(len(near) - 2)):
        flags.add("structuring")
    big_ins = [x for x in ins if x.amount_eur > 500]
    if (
        sum(
            any(0 < o.hour - i.hour <= 48 and 0.8 * i.amount_eur <= o.amount_eur <= i.amount_eur for o in outs)
            for i in big_ins
        )
        >= 2
    ):
        flags.add("pass_through")
    hours = sorted(ins, key=lambda x: x.hour)
    for i, first in enumerate(hours):
        window = [x for x in hours[i:] if x.hour - first.hour <= 14 * 24]
        if len(window) >= 20 and len({x.counterparty for x in window}) >= 15:
            flags.add("high_velocity_inbound")
            break
    out_value = sum(x.amount_eur for x in outs)
    by_cp: dict[str, float] = defaultdict(float)
    for x in outs:
        if x.country != c.country:
            by_cp[x.counterparty] += x.amount_eur
    if out_value and by_cp and max(by_cp.values()) / out_value >= 0.7:
        flags.add("funnel_outbound")
    if any(x.country in t["high_risk_jurisdictions"] for x in c.transfers):
        flags.add("high_risk_jurisdiction")
    months = max(1.0, (max((x.hour for x in c.transfers), default=0) / 720))
    monthly = sum(x.amount_eur for x in ins) / months
    persons = Counter(x.counterparty.split("-")[0] for x in ins)
    if monthly >= 3 * c.declared_monthly_eur or (
        c.declared in LOW_VOLUME_OCCUPATIONS and (persons["Person"] >= 15 or c.typology == "crypto_offramp")
    ):
        flags.add("profile_mismatch")
    crypto = sum(x.amount_eur for x in outs if x.counterparty in EXCHANGES + NEW_EXCHANGES)
    if out_value and crypto / out_value >= 0.3:
        flags.add("crypto_offramp")
    return flags


def risk_of(flags: set[str], c: Case) -> str:
    t = TAXONOMY
    mitigated: set[str] = set()
    who = MITIGATING_DECLARATION.get(c.declared)
    if who and c.documents_on_file:
        mitigated = set(t["risk"]["mitigations"].get(who, []))
    score = sum(t["flags"][f]["severity"] for f in flags if f not in mitigated)
    if score >= t["risk"]["high_at"]:
        return "high"
    return "medium" if score >= t["risk"]["medium_at"] else "low"


def label(c: Case) -> None:
    c.truth_flags = _flags(c)
    c.truth_risk = risk_of(c.truth_flags, c)
    c.truth_documents = {TAXONOMY["flags"][f]["document"] for f in c.truth_flags} if c.truth_risk != "low" else set()
