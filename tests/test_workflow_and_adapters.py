import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from edd.claude import ClaudeDraftModel
from edd.features import facts
from edd.prompts import PromptConfig
from edd.workflow import Outbox, answer, build, start
from edd_world.llm import SimulatedModel


def test_no_customer_is_contacted_before_an_analyst_approves(world_cases, records):
    model = SimulatedModel({c.id: c for c in world_cases})
    outbox = Outbox()
    g = build(model, PromptConfig(indicators=True), outbox)
    r = next(r for r, c in zip(records, world_cases) if c.truth_risk == "high")
    state = start(g, r)
    assert "__interrupt__" in state and outbox.sent == []
    proposed = state["__interrupt__"][0].value["draft"]["documents"]
    approved = proposed[:1] or ["source_of_funds"]
    answer(g, r.id, {"approved": True, "documents": approved})
    assert outbox.sent == [(r.id, approved)]


def test_a_rejected_draft_contacts_nobody(world_cases, records):
    model = SimulatedModel({c.id: c for c in world_cases})
    outbox = Outbox()
    g = build(model, PromptConfig(), outbox)
    start(g, records[1])
    answer(g, records[1].id, {"approved": False})
    assert outbox.sent == []


class FakeAnthropic:
    def __init__(self, payload):
        self.payload, self.requests = payload, []
        self.messages = SimpleNamespace(create=self.create)

    def create(self, **req):
        self.requests.append(req)
        block = SimpleNamespace(type="tool_use", input=self.payload)
        return SimpleNamespace(content=[block], usage=SimpleNamespace(input_tokens=1500, output_tokens=400))


def test_the_claude_adapter_forces_the_schema_tool_and_caches_the_system_prompt(records):
    r = records[0]
    payload = {"summary": "s", "facts": facts(r), "flags": [], "risk": "low", "documents": []}
    client = FakeAnthropic(payload)
    text, usage = ClaudeDraftModel(client).complete("sys", "user", PromptConfig(output="tool_schema"), r.id)
    req = client.requests[0]
    assert json.loads(text) == payload and usage.input_tokens == 1500
    assert req["tool_choice"] == {"type": "tool", "name": "edd_draft"} and req["model"] == "claude-sonnet-4-5"
    assert req["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_the_api_drafts_and_records_reviews(world_cases, records):
    import edd.api as api

    api.app.dependency_overrides[api.model] = lambda: SimulatedModel({c.id: c for c in world_cases})
    c = TestClient(api.app)
    assert c.get("/healthz").json() == {"ok": True}
    d = c.post("/drafts", json=records[2].model_dump()).json()
    assert d["status"] in ("draft", "no_draft") and "Risk:" in (d["text"] or "Risk:")
    assert c.post("/reviews", json={"draft_text": "Risk: low", "final_text": "Risk: high"}).json() == {
        "edit": "factual"
    }
    api.app.dependency_overrides.clear()
