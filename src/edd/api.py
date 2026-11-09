"""The workbench as a service: drafts for the case-management system, analyst decisions back.

uvicorn edd.api:app     (EDD_MODEL=claude uses the Anthropic API; credentials from the environment)
"""

from __future__ import annotations

import os
from functools import cache

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from edd.edits import classify
from edd.pipeline import draft
from edd.ports import DraftModel
from edd.prompts import PromptConfig
from edd.render import render
from edd.schema import CaseRecord

app = FastAPI(title="edd-case-intelligence", version="1.0.0")
PRODUCTION = PromptConfig(cot=True, indicators=True)


@cache
def model() -> DraftModel:
    if os.environ.get("EDD_MODEL") == "claude":
        import anthropic

        from edd.claude import ClaudeDraftModel

        return ClaudeDraftModel(anthropic.Anthropic())
    raise RuntimeError("set EDD_MODEL=claude (or override the dependency in tests)")


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.post("/drafts")
def make_draft(case: CaseRecord, m: DraftModel = Depends(model)) -> dict:
    d = draft(case, m, PRODUCTION)
    return {**d.to_dict(), "text": render(d.summary, list(d.flags), d.risk, d.documents) if d.status == "draft" else ""}


class Review(BaseModel):
    draft_text: str
    final_text: str


@app.post("/reviews")
def review(r: Review) -> dict:
    """Record an analyst's final version; the edit kind feeds the quality monitor."""
    return {"edit": classify(r.draft_text, r.final_text)}
