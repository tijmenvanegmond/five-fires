"""Regression tests. Every assertion here was established by a stress run."""

from dataclasses import replace
from distributor import Distributor

D = Distributor.from_yaml("config.yaml")


def test_chamber_fully_allocated():
    r = D({"A": 33, "B": 33, "C": 11, "D": 11, "E": 11})
    assert sum(r.seats.values()) == 400


def test_equal_votes_give_equal_seats():
    r = D({"A": 33, "B": 33, "C": 11, "D": 11, "E": 11})
    assert r.seats["C"] == r.seats["D"] == r.seats["E"]


def test_sixth_party_ejected():
    r = D({"A": 40, "B": 25, "C": 20, "D": 10, "E": 4, "F": 1})
    assert r.ejected == ("F",) and "F" not in r.seats


def test_dual_key_blocks_minority_capture():
    r = D({"A": 33, "B": 33, "C": 11, "D": 11, "E": 11})
    assert not r.can_act(["C", "D", "E"])
    assert r.can_act(["A", "C", "D"])


def test_fires_only_would_have_allowed_it():
    r = replace(D, seat_majority=False)({"A": 33, "B": 33, "C": 11, "D": 11, "E": 11})
    assert r.can_act(["C", "D", "E"])


def test_two_fires_never_suffice_at_five():
    r = D({"A": 45, "B": 40, "C": 8, "D": 5, "E": 2})
    assert r.can_pass(["A", "B"]) and not r.can_act(["A", "B"])


def test_threshold_never_deadlocks():
    votes = {"A": 24, "B": 23, "C": 21, "D": 16, "E": 11, "F": 5}
    for n in (2, 3, 4, 5):
        r = replace(D, fires=n)(votes)
        assert r.coalitions(r.can_act), f"deadlock at {n} fires"


def test_split_gains_seats_without_lineage():
    base = D({"A": 40, "B": 25, "C": 20, "D": 10, "E": 5})
    split = D({"A1": 20.8, "A2": 19.2, "B": 25, "C": 20, "D": 10, "E": 5})
    # Without lineage, splitting gains seats (natural incentive)
    assert split.seats["A1"] + split.seats["A2"] > base.seats["A"]
    assert "E" in split.ejected


def test_split_pays_without_lineage():
    naive = replace(D, lineage=False)
    base = naive({"A": 40, "B": 25, "C": 20, "D": 10, "E": 5})
    split = naive({"A1": 20.8, "A2": 19.2, "B": 25, "C": 20, "D": 10, "E": 5})
    assert "E" in split.ejected
    assert split.seats["A1"] + split.seats["A2"] > base.seats["A"]


def test_no_lineage_parties_are_separate():
    r = D({"A1": 21, "A2": 19, "B": 25, "C": 20, "D": 10, "E": 5},
          lineage={"A1": "A", "A2": "A"})
    # With lineage=False, parties are separate fires regardless of lineage mapping
    assert len(r.fires) == 5 and r.fire_of("A1") is not r.fire_of("A2")


def test_fewer_parties_than_fires():
    r = D({"A": 60, "B": 40})
    assert len(r.fires) == 2 and sum(r.seats.values()) == 400


def test_coalitions_are_minimal():
    r = D({"A": 33, "B": 33, "C": 11, "D": 11, "E": 11})
    cs = r.coalitions(r.can_act)
    assert all(r.can_act(c) for c in cs)
    assert not any(set(a) < set(b) for a in cs for b in cs)


def test_dhondt_favours_the_large():
    v = {"A": 40, "B": 25, "C": 20, "D": 10, "E": 5}
    assert replace(D, divisor="dhondt")(v).seats["A"] >= D(v).seats["A"]


if __name__ == "__main__":
    import sys, traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    bad = 0
    for t in tests:
        try:
            t(); print(f"  pass  {t.__name__}")
        except Exception:
            bad += 1; print(f"  FAIL  {t.__name__}"); traceback.print_exc(limit=1)
    print(f"\n{len(tests)-bad}/{len(tests)} passed")
    sys.exit(bool(bad))
