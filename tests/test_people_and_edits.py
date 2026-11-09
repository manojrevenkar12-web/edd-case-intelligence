from edd.edits import classify
from edd.render import render
from edd_world.people import analyst_review, annotate


def test_edits_are_split_into_factual_and_stylistic():
    before = render("Received EUR 1,000.00 and sent EUR 500.00.", ["structuring"], "high", ["source_of_funds"])
    assert classify(before, before) == "none"
    assert classify(before, before.replace("Received", "Got")) == "stylistic"
    assert classify(before, render("Received EUR 1,000.00 and sent EUR 500.00.", [], "low", [])) == "factual"
    assert classify(before, before.replace("1,000.00", "1,200.00")) == "factual"


def test_the_classifier_agrees_with_what_the_analysts_actually_did(world_cases):
    for c in world_cases[:120]:
        draft_text = render("Received EUR 10.00.", sorted(c.truth_flags), c.truth_risk, sorted(c.truth_documents))
        after, _ = analyst_review(c, draft_text)
        assert classify(draft_text, after) in ("none", "stylistic")  # a correct draft is never a factual edit
        wrong = render("Received EUR 10.00.", [], "low", [])
        after, dec = analyst_review(c, wrong)
        expected = "factual" if (dec["flags"] or dec["risk"] != "low") else classify(wrong, after)
        assert classify(wrong, after) == expected


def test_the_two_smes_disagree_where_the_guideline_is_open(world_cases):
    a = [annotate(c, "sme_a") for c in world_cases]
    b = [annotate(c, "sme_b") for c in world_cases]
    diff = sum(x.flags != y.flags for x, y in zip(a, b))
    assert 0 < diff < len(world_cases) // 2
