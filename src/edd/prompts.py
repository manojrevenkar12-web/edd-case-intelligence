"""Prompt configurations and the context they build. Every experiment changes one of these fields."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from edd.features import COMPUTED, facts, indicators
from edd.schema import CaseRecord
from edd.taxonomy import taxonomy


@dataclass(frozen=True)
class PromptConfig:
    model: str = "anthropic.claude-sonnet-4-5"
    few_shot: int = 0  # worked examples from the golden set
    few_shot_set: str = "v1"  # which examples (v2 adds the typologies seen since)
    cot: bool = False  # reason step by step before answering
    context_order: str = "raw"  # raw | chronological | aggregated_first
    output: str = "json_text"  # json_text | tool_schema
    indicators: bool = False  # give the model the computed indicators and ask it only for the rest

    def key(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    def as_dict(self) -> dict:
        return asdict(self)


SYSTEM = """You prepare enhanced due diligence drafts for a financial crime analyst. You never decide: the analyst
does. Return a summary, the facts you relied on, the red flags whose definition is met (each with the ids of the
transfers that show it), a risk class from the taxonomy's rule, and the documents to request."""


def context(case: CaseRecord, cfg: PromptConfig) -> str:
    """The user message: taxonomy, customer, then the transfers in the configured order."""
    t = taxonomy()
    parts = ["Taxonomy:"] + [f"- {k}: {v['definition']}" for k, v in t["flags"].items()]
    parts.append(
        f"Customer: {case.kind}, {case.country}, declared '{case.declared}', "
        f"about EUR {case.declared_monthly_eur:,.0f} "
        f"a month, account {case.account_age_months} months old, documents on file: {case.documents_on_file}."
    )
    txs = case.transfers if cfg.context_order == "raw" else sorted(case.transfers, key=lambda x: x.hour)
    if cfg.context_order == "aggregated_first":
        parts.append("Computed facts: " + json.dumps(facts(case)))
    if cfg.indicators:
        found = {i.flag: i.evidence for i in indicators(case)}
        parts.append("Computed indicators (exact; copy them): " + json.dumps(found))
        parts.append(f"Assess only: {[f for f in t['flags'] if f not in COMPUTED]}, then risk and documents.")
    parts.append("Transfers:")
    parts += [
        f"{x.id} h{x.hour:.0f} {x.direction} EUR {x.amount_eur:,.2f} {x.counterparty} {x.country} '{x.reference}'"
        for x in txs
    ]
    if cfg.cot:
        parts.append("Think through each flag's definition step by step before you answer.")
    return "\n".join(parts)
