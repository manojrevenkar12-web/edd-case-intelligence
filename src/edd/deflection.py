"""Demand deflection: find the customers who will become high-risk EDD cases from what is known in their first
week, so a document request at that point stops the activity before it ever reaches the operations team.

The model is a gradient-boosted classifier on first-week features. It is judged as a policy: at a given share
of good customers asked for documents (friction), what share of the future high-risk cases does it catch?
"""

from __future__ import annotations

from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd

from edd.schema import CaseRecord
from edd.taxonomy import taxonomy

FIRST_WEEK_H = 7 * 24


def first_week(c: CaseRecord) -> dict[str, float]:
    t = taxonomy()
    week = [x for x in c.transfers if x.hour < FIRST_WEEK_H]
    ins = [x for x in week if x.direction == "in"]
    outs = [x for x in week if x.direction == "out"]
    thr = t["reporting_threshold_eur"]
    return {
        "business": float(c.kind == "business"),
        "declared_monthly_eur": c.declared_monthly_eur,
        "documents_on_file": float(c.documents_on_file),
        "in_count": len(ins),
        "in_eur": sum(x.amount_eur for x in ins),
        "distinct_senders": len({x.counterparty for x in ins}),
        "out_count": len(outs),
        "out_eur": sum(x.amount_eur for x in outs),
        "abroad_out_share": sum(x.country != c.country for x in outs) / max(1, len(outs)),
        "near_threshold": sum(0.9 * thr <= x.amount_eur < thr for x in ins),
        "hrj": float(any(x.country in t["high_risk_jurisdictions"] for x in week)),
        "top_ups": sum("top up" in x.reference for x in outs),
        "in_vs_declared": sum(x.amount_eur for x in ins) * 4.3 / max(1.0, c.declared_monthly_eur),
    }


@dataclass
class DeflectionModel:
    booster: lgb.Booster
    columns: list[str]

    def score(self, cases: list[CaseRecord]) -> np.ndarray:
        x = pd.DataFrame([first_week(c) for c in cases])[self.columns]
        return self.booster.predict(x)


def train(cases: list[CaseRecord], labels: np.ndarray, seed: int = 3) -> DeflectionModel:
    x = pd.DataFrame([first_week(c) for c in cases])
    params = {
        "objective": "binary",
        "num_leaves": 15,
        "learning_rate": 0.05,
        "min_data_in_leaf": 40,
        "feature_fraction": 0.9,
        "seed": seed,
        "verbose": -1,
        "num_threads": 2,
        "scale_pos_weight": float((labels == 0).sum() / max(1, labels.sum())),
    }
    booster = lgb.train(params, lgb.Dataset(x, labels), num_boost_round=250)
    return DeflectionModel(booster, list(x.columns))


def rule_baseline(cases: list[CaseRecord]) -> np.ndarray:
    """What a rules team would write first: any high-risk jurisdiction, near-threshold deposit or exchange top-up."""
    f = [first_week(c) for c in cases]
    return np.array([x["hrj"] + x["near_threshold"] + x["top_ups"] + (x["distinct_senders"] >= 8) for x in f], float)


def policy_curve(scores: np.ndarray, labels: np.ndarray, budgets: list[float]) -> list[dict]:
    """At each friction budget (share of good customers asked for documents), the share of future high-risk
    cases caught."""
    good = np.sort(scores[labels == 0])[::-1]
    out = []
    for b in budgets:
        k = max(1, round(b * len(good)))
        cut = good[k - 1]
        caught = int((scores[labels == 1] >= cut).sum())
        asked_good = int((scores[labels == 0] >= cut).sum())
        out.append(
            {
                "friction": b,
                "good_asked": asked_good,
                "caught": caught,
                "positives": int(labels.sum()),
                "recall": caught / max(1, int(labels.sum())),
                "precision": caught / max(1, caught + asked_good),
            }
        )
    return out
