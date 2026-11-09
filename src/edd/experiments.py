"""Hypothesis-driven prompt experiments: pre-registered in experiments/registry.yaml, estimated on the
development split, tested once on the held-out split with a Holm correction across the family."""

from __future__ import annotations

from dataclasses import replace

import yaml

from edd.evals import Label, holm, paired
from edd.pipeline import Draft, draft
from edd.ports import DraftModel
from edd.prompts import PromptConfig
from edd.schema import CaseRecord
from edd.settings import settings
from edd.taxonomy import ROOT


def registry() -> dict:
    return yaml.safe_load((ROOT / "experiments" / "registry.yaml").read_text())


def baseline() -> PromptConfig:
    return PromptConfig(**registry()["baseline"])


class Runner:
    """Drafts each configuration once per case and caches them, so experiments sharing a configuration agree."""

    def __init__(self, cases: list[CaseRecord], model: DraftModel):
        self.cases, self.model = cases, model
        self.cache: dict[str, list[Draft]] = {}

    def drafts(self, cfg: PromptConfig) -> list[Draft]:
        if cfg.key() not in self.cache:
            self.cache[cfg.key()] = [draft(c, self.model, cfg) for c in self.cases]
        return self.cache[cfg.key()]


def run(runner: Runner, labels: dict[str, Label], seed: int = 0) -> list[dict]:
    reg = registry()
    base = baseline()
    out = []
    for e in reg["experiments"]:
        a_cfg = replace(base, **e.get("against", {}))
        b_cfg = replace(a_cfg, **e["change"])
        r = paired(
            runner.drafts(a_cfg),
            runner.drafts(b_cfg),
            labels,
            e["metric"],
            settings()["experiments"]["bootstrap"],
            seed,
        )
        sign = 1 if e["direction"] == "greater" else -1
        one_sided = r["p"] / 2 if sign * r["effect"] > 0 else 1 - r["p"] / 2
        out.append({**e, **r, "p_one_sided": one_sided})
    rejected = holm([x["p_one_sided"] for x in out], settings()["experiments"]["alpha"])
    for x, rej in zip(out, rejected):
        x["confirmed"] = bool(rej)
    return out
