"""Post-deployment monitoring, week by week, from what production records: case features, the drafts' outputs
and the analysts' edits. No labels are needed to raise an alert; labels arrive later through the edits.

- Input drift: population stability index of case features against the baseline weeks.
- Output drift: each flag's rate and the risk mix against the baseline (two-proportion test).
- Quality: the factual-edit rate on a p-chart with 3-sigma limits from the baseline weeks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from edd.schema import CaseRecord
from edd.settings import settings


def case_features(c: CaseRecord) -> dict[str, float]:
    ins = [t for t in c.transfers if t.direction == "in"]
    outs = [t for t in c.transfers if t.direction == "out"]
    out_value = sum(t.amount_eur for t in outs) or 1.0
    return {
        "transfers": len(c.transfers),
        "distinct_senders": len({t.counterparty for t in ins}),
        "inbound_share": len(ins) / max(1, len(c.transfers)),
        "top_up_share": sum(t.amount_eur for t in outs if "top up" in t.reference) / out_value,
    }


def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)[1:-1]))
    e = np.bincount(np.searchsorted(edges, expected, side="right"), minlength=len(edges) + 1) / len(expected)
    a = np.bincount(np.searchsorted(edges, actual, side="right"), minlength=len(edges) + 1) / len(actual)
    e, a = np.maximum(e, 1e-4), np.maximum(a, 1e-4)
    return float(np.sum((a - e) * np.log(a / e)))


@dataclass
class WeekReport:
    week: int
    cases: int
    factual_edit_rate: float
    stylistic_edit_rate: float
    edit_ucl: float
    psi: dict[str, float]
    flag_rates: dict[str, float]
    alerts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class Monitor:
    def __init__(self, baseline_weeks: int):
        self.baseline_weeks = baseline_weeks
        self.base_features: dict[str, list[float]] = {}
        self.base_edits = [0, 0]
        self.base_flags: dict[str, list[int]] = {}

    def observe(self, week: int, cases: list[CaseRecord], flags: list[set[str]], edit_kinds: list[str]) -> WeekReport:
        cfg = settings()["monitor"]
        feats = [case_features(c) for c in cases]
        n = len(cases)
        fact = sum(k == "factual" for k in edit_kinds)
        style = sum(k == "stylistic" for k in edit_kinds)
        names = sorted({f for fs in flags for f in fs} | set(self.base_flags))
        rates = {f: sum(f in fs for fs in flags) / n for f in names}
        if week <= self.baseline_weeks:
            for k in feats[0]:
                self.base_features.setdefault(k, []).extend(x[k] for x in feats)
            self.base_edits[0] += fact
            self.base_edits[1] += n
            for f in names:
                self.base_flags.setdefault(f, [0, 0])
                self.base_flags[f][0] += sum(f in fs for fs in flags)
                self.base_flags[f][1] += n
            return WeekReport(week, n, fact / n, style / n, float("nan"), {}, rates, [])
        p0 = self.base_edits[0] / self.base_edits[1]
        ucl = p0 + 3 * math.sqrt(p0 * (1 - p0) / n)
        rep = WeekReport(
            week,
            n,
            fact / n,
            style / n,
            ucl,
            {k: psi(np.array(v), np.array([x[k] for x in feats])) for k, v in self.base_features.items()},
            rates,
        )
        if fact / n > ucl:
            rep.alerts.append(f"factual edits {fact / n:.1%} above the control limit {ucl:.1%}")
        for k, v in rep.psi.items():
            if v > cfg["psi_alert"]:
                rep.alerts.append(f"input drift on {k} (PSI {v:.2f})")
        for f, (k, m) in self.base_flags.items():
            p_base, p_now = k / m, rates.get(f, 0.0)
            se = math.sqrt(max(1e-9, p_base * (1 - p_base) * (1 / m + 1 / n)))
            if abs(p_now - p_base) / se > cfg["flag_rate_z"]:
                rep.alerts.append(f"{f} rate {p_now:.1%} vs {p_base:.1%} at baseline")
        return rep
