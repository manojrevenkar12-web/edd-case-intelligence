from edd.features import COMPUTED, evidence_holds, facts, indicators


def test_computed_indicators_match_the_taxonomy_definitions(world_cases, records):
    for c, r in zip(world_cases, records):
        assert {i.flag for i in indicators(r)} == c.truth_flags & set(COMPUTED), c.id


def test_every_indicator_carries_evidence_that_passes_its_own_check(records):
    for r in records:
        for i in indicators(r):
            assert evidence_holds(r, i.flag, i.evidence), (r.id, i.flag)


def test_evidence_that_does_not_exist_or_does_not_show_the_pattern_is_refused(records):
    r = next(r for r in records if any(i.flag == "structuring" for i in indicators(r)))
    small = [t.id for t in r.transfers if t.amount_eur < 100][:3]
    assert not evidence_holds(r, "structuring", small)
    assert not evidence_holds(r, "structuring", [f"{r.id}-t999"])
    assert not evidence_holds(r, "high_risk_jurisdiction", small)


def test_facts_are_sums_of_the_transfers(records):
    r = records[0]
    f = facts(r)
    assert f["transfers"] == len(r.transfers)
    assert abs(f["total_in_eur"] - sum(t.amount_eur for t in r.transfers if t.direction == "in")) < 0.01
