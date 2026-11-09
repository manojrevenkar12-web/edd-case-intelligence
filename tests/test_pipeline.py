import json

from edd.features import facts, indicators
from edd.pipeline import draft
from edd.ports import Usage
from edd.prompts import PromptConfig


class Scripted:
    """A model that returns what a test tells it to."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def complete(self, system, user, cfg, case_id):
        self.calls += 1
        return self.replies.pop(0), Usage(1000, 300, 900.0)


def _reply(r, **over):
    f = facts(r)
    out = {
        "summary": f"Received EUR {f['total_in_eur']:,.2f} and sent EUR {f['total_out_eur']:,.2f} "
        f"across {f['transfers']} transfers.",
        "facts": f,
        "flags": [],
        "risk": "low",
        "documents": [],
    }
    out.update(over)
    return json.dumps(out)


def test_a_bad_format_is_retried_once_then_the_case_goes_to_the_analyst_without_a_draft(records):
    r = records[0]
    m = Scripted(["Here is the draft: {", "not json"])
    d = draft(r, m, PromptConfig())
    assert d.status == "no_draft" and m.calls == 2 and d.format_retries == 2
    m = Scripted(["oops", _reply(r)])
    assert draft(r, m, PromptConfig()).status == "draft"


def test_flags_without_real_evidence_are_dropped_with_a_reason(records):
    r = records[0]
    bogus = [
        {"flag": "structuring", "evidence": [f"{r.id}-t999"]},
        {"flag": "made_up", "evidence": [r.transfers[0].id]},
    ]
    d = draft(r, Scripted([_reply(r, flags=bogus)]), PromptConfig())
    assert d.flags == {} and {x[0] for x in d.dropped} == {"structuring", "made_up"}


def test_a_wrong_number_is_corrected_in_the_facts_and_the_summary(records):
    r = records[0]
    f = facts(r)
    wrong = dict(f, total_in_eur=f["total_in_eur"] * 2)
    summary = f"Received EUR {wrong['total_in_eur']:,.2f} across {f['transfers']} transfers."
    d = draft(r, Scripted([_reply(r, facts=wrong, summary=summary)]), PromptConfig())
    assert d.corrected_facts == ["total_in_eur"] and f"{f['total_in_eur']:,.2f}" in d.summary


def test_risk_below_the_flags_needs_a_verified_business(records):
    r = next(r for r in records if not r.documents_on_file and len(indicators(r)) >= 2)
    flags = [{"flag": i.flag, "evidence": i.evidence} for i in indicators(r)]
    d = draft(r, Scripted([_reply(r, flags=flags, risk="low")]), PromptConfig())
    assert d.raised_risk and d.risk in ("medium", "high")
    assert len(d.documents) >= 1


def test_with_indicators_code_adds_what_the_model_missed(records):
    r = next(r for r in records if indicators(r))
    d = draft(r, Scripted([_reply(r, flags=[])]), PromptConfig(indicators=True))
    assert set(d.added_indicators) == {i.flag for i in indicators(r)}
