"""The shapes the workbench works with: a case as the case-management system holds it, and the draft the
model must return. The draft schema is strict: anything else is a format error."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Risk = Literal["low", "medium", "high"]


class TransferRecord(BaseModel):
    id: str
    hour: float
    direction: Literal["in", "out"]
    amount_eur: float
    counterparty: str
    country: str
    reference: str


class CaseRecord(BaseModel):
    """What an EDD case holds when it lands on an analyst's screen. No outcome, no label."""

    id: str
    week: int
    kind: Literal["consumer", "business"]
    country: str
    declared: str
    declared_monthly_eur: float
    account_age_months: int
    documents_on_file: bool
    transfers: list[TransferRecord]


class FlagClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    flag: str
    evidence: list[str] = Field(min_length=1)
    rationale: str = ""


class Facts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_in_eur: float
    total_out_eur: float
    transfers: int
    largest_counterparty: str


class DraftOutput(BaseModel):
    """What the model must return."""

    model_config = ConfigDict(extra="forbid")
    summary: str
    facts: Facts
    flags: list[FlagClaim]
    risk: Risk
    documents: list[str]
