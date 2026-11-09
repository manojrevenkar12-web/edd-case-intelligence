"""The case workflow as a LangGraph graph with a person in the loop.

    draft ─► analyst review (interrupt) ─► approved? ─► request documents ─► done
                                             └─ rejected ─► done (no contact)

The graph stops at the review node and waits, checkpointed, until an analyst answers. The only action with an
effect outside the workbench (asking the customer for documents) runs after an approval, with the documents the
analyst approved, not the ones the model proposed.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command, interrupt

from edd.pipeline import draft
from edd.ports import DraftModel
from edd.prompts import PromptConfig
from edd.schema import CaseRecord


class CaseState(TypedDict, total=False):
    case: dict
    draft: dict
    decision: dict
    requested: list[str]


class Outbox:
    """Where customer contact would go. Tests read it to prove nothing is sent without approval."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, list[str]]] = []

    def request_documents(self, case_id: str, documents: list[str]) -> None:
        self.sent.append((case_id, documents))


def build(model: DraftModel, cfg: PromptConfig, outbox: Outbox):
    def make_draft(s: CaseState) -> CaseState:
        d = draft(CaseRecord.model_validate(s["case"]), model, cfg)
        return {"draft": d.to_dict()}

    def review(s: CaseState) -> CaseState:
        answer: dict[str, Any] = interrupt({"draft": s["draft"], "ask": "approve, edit or reject"})
        return {"decision": answer}

    def route(s: CaseState) -> str:
        return "request" if s["decision"].get("approved") and s["decision"].get("documents") else END

    def request(s: CaseState) -> CaseState:
        docs = list(s["decision"]["documents"])
        outbox.request_documents(s["case"]["id"], docs)
        return {"requested": docs}

    g = StateGraph(CaseState)
    g.add_node("draft", make_draft)
    g.add_node("review", review)
    g.add_node("request", request)
    g.set_entry_point("draft")
    g.add_edge("draft", "review")
    g.add_conditional_edges("review", route, {"request": "request", END: END})
    g.add_edge("request", END)
    return g.compile(checkpointer=MemorySaver())


def start(graph, case: CaseRecord) -> dict:
    cfg = {"configurable": {"thread_id": case.id}}
    return graph.invoke({"case": case.model_dump()}, cfg)


def answer(graph, case_id: str, decision: dict) -> dict:
    return graph.invoke(Command(resume=decision), {"configurable": {"thread_id": case_id}})
