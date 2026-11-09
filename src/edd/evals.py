"""The eval harness: drafts against labels, by flag, by risk class and by failure mode, with intervals.

Labels come from the adjudicated golden set (two SMEs and a guideline), never from the model. Every rate is
reported with a 95% Wilson interval; every comparison between two configurations is paired, case by case.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

import numpy as np

from edd.pipeline import RISK_ORDER, Draft
from edd.taxonomy import flag_names

Z = 1.959963984540054


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


@dataclass
class Label:
    case_id: str
    flags: set[str]
    risk: str
    documents: set[str]


def case_correct(d: Draft, y: Label) -> bool:
    """The strict case-level outcome: right flags and right risk class."""
    return d.status == "draft" and set(d.flags) == y.flags and d.risk == y.risk


def failure_modes(d: Draft, y: Label) -> list[str]:
    if d.status != "draft":
        return ["format"]
    modes = []
    s = set(d.flags)
    if y.flags - s:
        modes.append("missed_flag")
    if s - y.flags:
        modes.append("false_flag")
    if d.dropped:
        modes.append("unsupported_evidence")
    if d.corrected_facts:
        modes.append("wrong_fact")
    if RISK_ORDER[d.risk] < RISK_ORDER[y.risk]:
        modes.append("risk_too_low")
    elif RISK_ORDER[d.risk] > RISK_ORDER[y.risk]:
        modes.append("risk_too_high")
    return modes


def evaluate(drafts: list[Draft], labels: dict[str, Label]) -> dict:
    per_flag = {}
    for f in flag_names():
        tp = sum(f in d.flags and f in labels[d.case_id].flags for d in drafts)
        fp = sum(f in d.flags and f not in labels[d.case_id].flags for d in drafts)
        fn = sum(f not in d.flags and f in labels[d.case_id].flags for d in drafts)
        per_flag[f] = {
            "support": tp + fn,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "recall_ci": wilson(tp, tp + fn),
        }
    tp = sum(len(set(d.flags) & labels[d.case_id].flags) for d in drafts)
    fp = sum(len(set(d.flags) - labels[d.case_id].flags) for d in drafts)
    fn = sum(len(labels[d.case_id].flags - set(d.flags)) for d in drafts)
    n = len(drafts)
    high = [d for d in drafts if labels[d.case_id].risk == "high"]
    high_found = sum(d.risk == "high" for d in high)
    risk_ok = sum(d.status == "draft" and d.risk == labels[d.case_id].risk for d in drafts)
    correct = sum(case_correct(d, labels[d.case_id]) for d in drafts)
    modes = Counter(m for d in drafts for m in failure_modes(d, labels[d.case_id]))
    return {
        "cases": n,
        "flag_precision": tp / (tp + fp) if tp + fp else 0.0,
        "flag_recall": tp / (tp + fn) if tp + fn else 0.0,
        "flag_f1": 2 * tp / (2 * tp + fp + fn) if tp else 0.0,
        "risk_accuracy": risk_ok / n,
        "risk_accuracy_ci": wilson(risk_ok, n),
        "high_risk_recall": high_found / len(high) if high else None,
        "high_risk_recall_ci": wilson(high_found, len(high)),
        "case_correct": correct / n,
        "case_correct_ci": wilson(correct, n),
        "no_draft_rate": sum(d.status != "draft" for d in drafts) / n,
        "unsupported_evidence_rate": sum(bool(d.dropped) for d in drafts) / n,
        "wrong_fact_rate": sum(bool(d.corrected_facts) for d in drafts) / n,
        "risk_raised_by_check": sum(d.raised_risk for d in drafts) / n,
        "cost_per_case_usd": float(np.mean([d.cost_usd for d in drafts])),
        "p95_latency_ms": float(np.percentile([d.latency_ms for d in drafts], 95)),
        "failure_modes": dict(modes.most_common()),
        "per_flag": per_flag,
    }


def paired(
    a: list[Draft], b: list[Draft], labels: dict[str, Label], metric: str, resamples: int = 2000, seed: int = 0
) -> dict:
    """b minus a on a per-case metric, with a paired bootstrap interval."""

    def score(d: Draft) -> float:
        y = labels[d.case_id]
        if metric == "case_correct":
            return float(case_correct(d, y))
        if metric == "risk_correct":
            return float(d.status == "draft" and d.risk == y.risk)
        if metric == "wrong_fact":
            return float(bool(d.corrected_facts) or d.status != "draft")
        if metric == "flag_errors":
            return float(len(set(d.flags) ^ y.flags))
        if metric.startswith("recall:"):
            f = metric.split(":", 1)[1]
            return float(f in d.flags) if f in y.flags else np.nan
        raise ValueError(metric)

    sa = np.array([score(d) for d in a])
    sb = np.array([score(d) for d in b])
    keep = ~(np.isnan(sa) | np.isnan(sb))
    diff = sb[keep] - sa[keep]
    rng = np.random.default_rng(seed)
    boots = diff[rng.integers(0, len(diff), (resamples, len(diff)))].mean(axis=1)
    # two-sided bootstrap p-value for "no difference"
    p = 2 * min((boots <= 0).mean(), (boots >= 0).mean())
    return {
        "metric": metric,
        "n": int(keep.sum()),
        "effect": float(diff.mean()),
        "ci": (float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))),
        "p": float(min(1.0, p)),
    }


def holm(pvalues: list[float], alpha: float = 0.05) -> list[bool]:
    """Holm–Bonferroni: which hypotheses are rejected, controlling the family-wise error rate."""
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    rejected = [False] * len(pvalues)
    for rank, i in enumerate(order):
        if pvalues[i] <= alpha / (len(pvalues) - rank):
            rejected[i] = True
        else:
            break
    return rejected
