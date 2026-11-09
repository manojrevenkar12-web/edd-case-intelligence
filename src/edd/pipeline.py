"""One structured pipeline per case: context → model → schema → checks → draft for the analyst.

The model reads; code checks. A draft reaches an analyst only after:
- the output parsed against the strict schema (one retry, then the case goes to the analyst without a draft);
- every flag's cited transfers exist and show the pattern (otherwise the flag is dropped, with the reason);
- every number in the facts matches what code computes from the transfers (otherwise it is corrected);
- the computed indicators are present (code adds any the model missed, when the configuration uses them);
- a lower risk than the flags imply is kept only if the mitigating context is verified (documents on file);
- the documents requested cover every flag kept.
The analyst decides; nothing here closes a case or contacts a customer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from pydantic import ValidationError

from edd.cost import usd
from edd.features import evidence_holds, facts, indicators
from edd.ports import DraftModel
from edd.prompts import SYSTEM, PromptConfig, context
from edd.schema import CaseRecord, DraftOutput, FlagClaim
from edd.taxonomy import document_for, flag_names, taxonomy

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


@dataclass
class Draft:
    case_id: str
    status: str  # "draft" or "no_draft" (format failed twice)
    summary: str = ""
    facts: dict = field(default_factory=dict)
    flags: dict[str, list[str]] = field(default_factory=dict)
    risk: str = "low"
    documents: list[str] = field(default_factory=list)
    dropped: list[tuple[str, str]] = field(default_factory=list)
    corrected_facts: list[str] = field(default_factory=list)
    added_indicators: list[str] = field(default_factory=list)
    raised_risk: bool = False
    format_retries: int = 0
    raw_flags: list[str] = field(default_factory=list)  # what the model said, before the checks
    raw_risk: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


def _parse(text: str) -> DraftOutput:
    return DraftOutput.model_validate(json.loads(text))


def draft(case: CaseRecord, model: DraftModel, cfg: PromptConfig, checks: bool = True) -> Draft:
    user = context(case, cfg)
    d = Draft(case.id, "draft")
    out = None
    for attempt in range(2):
        text, usage = model.complete(SYSTEM, user if attempt == 0 else user + "\nReturn only valid JSON.", cfg, case.id)
        d.input_tokens += usage.input_tokens
        d.output_tokens += usage.output_tokens
        d.latency_ms += usage.latency_ms
        try:
            out = _parse(text)
            break
        except (json.JSONDecodeError, ValidationError):
            d.format_retries += 1
    d.cost_usd = usd(cfg.model, d.input_tokens, d.output_tokens)
    if out is None:
        d.status = "no_draft"
        return d

    d.raw_flags = [f.flag for f in out.flags]
    d.raw_risk = out.risk
    if not checks:  # for measuring what the checks catch: the model's output as it came
        d.summary, d.facts, d.risk, d.documents = out.summary, out.facts.model_dump(), out.risk, out.documents
        d.flags = {f.flag: f.evidence for f in out.flags if f.flag in flag_names()}
        return d

    kept: dict[str, list[str]] = {}
    for claim in out.flags:
        if claim.flag not in flag_names():
            d.dropped.append((claim.flag, "not in the taxonomy"))
        elif not evidence_holds(case, claim.flag, claim.evidence):
            d.dropped.append((claim.flag, "cited transfers missing or not showing the pattern"))
        else:
            kept[claim.flag] = claim.evidence
    if cfg.indicators:
        for ind in indicators(case):
            if ind.flag not in kept:
                kept[ind.flag] = ind.evidence
                d.added_indicators.append(ind.flag)
    d.flags = kept

    true_facts = facts(case)
    stated = out.facts.model_dump()
    summary = out.summary
    for k, v in true_facts.items():
        sv = stated.get(k)
        wrong = (
            (abs(float(sv) - float(v)) > 0.005 * max(1.0, abs(float(v)))) if isinstance(v, (int, float)) else sv != v
        )
        if wrong:
            d.corrected_facts.append(k)
            if isinstance(v, float):
                summary = summary.replace(f"{float(sv):,.2f}", f"{v:,.2f}")
            elif isinstance(v, int):
                summary = summary.replace(f"across {sv} transfers", f"across {v} transfers")
    d.summary, d.facts = summary, true_facts

    t = taxonomy()
    unmitigated = sum(t["flags"][f]["severity"] for f in kept)
    floor = (
        "high" if unmitigated >= t["risk"]["high_at"] else "medium" if unmitigated >= t["risk"]["medium_at"] else "low"
    )
    risk = out.risk
    if RISK_ORDER[risk] < RISK_ORDER[floor] and not case.documents_on_file:
        risk, d.raised_risk = floor, True  # mitigation needs a verified business, and there is none
    d.risk = risk
    docs = set(out.documents) if risk != "low" else set()
    if risk != "low":
        docs |= {document_for(f) for f in kept}
    d.documents = sorted(docs)
    return d


def claim(flag: str, evidence: list[str]) -> FlagClaim:
    return FlagClaim(flag=flag, evidence=evidence)
