"""Regression tests. Every assertion here was established by a stress run.

The ladder tests are the point of the file: they pin the incentives that the
manifesto argues for, so that a change to the rules that quietly reverses one
of them fails here instead of in an argument.
"""

from dataclasses import replace

from distributor import Distributor, divide, merge

D = Distributor.from_yaml("config.yaml")

# One dominant party, one mid, a long tail. The case the design exists for.
LOPSIDED = {"A": 40, "B": 20, "C": 8, "D": 7, "E": 1,
            "T1": 8, "T2": 7, "T3": 5, "T4": 4}


def fires_held(r, prefix):
    return sum(1 for f in r.fires if f.name.startswith(prefix))


def seats_of(r, prefix):
    return sum(s for p, s in r.seats.items() if p.startswith(prefix))


# ----------------------------------------------------------------- the basics

def test_chamber_is_conserved():
    r = D({"A": 33, "B": 33, "C": 11, "D": 11, "E": 11})
    assert sum(r.seats.values()) + r.cold == 400


def test_equal_votes_give_equal_seats():
    r = D({"A": 20, "B": 20, "C": 20, "D": 20, "E": 20})
    assert len(set(r.seats.values())) == 1 and r.cold == 0


def test_sixth_party_ejected():
    r = D({"A": 30, "B": 25, "C": 20, "D": 20, "E": 4, "F": 1})
    assert r.ejected == ("F",) and "F" not in r.seats


def test_fewer_parties_than_fires():
    r = D({"A": 60, "B": 40})
    assert len(r.fires) == 2 and sum(r.seats.values()) + r.cold == 400


# ------------------------------------------------- the divisor does NOT do it

def test_divisor_supplies_no_splitting_bonus():
    """The old claim was that Sainte-Lague rewards dividing. It does not.

    With no cap and no cliff, a party that divides holds exactly the seats
    it held before -- under either divisor. Every incentive to divide in
    this system comes from the cap.
    """
    whole = {"A": 40, "B": 20, "C": 20, "D": 15, "E": 5}
    split = divide(whole, "A", {"A1": 0.5, "A2": 0.5})
    for div in ("sainte_lague", "dhondt"):
        d = replace(D, divisor=div, cap=None, fires=6)
        assert seats_of(d(split), "A") == d(whole).seats["A"]


# ------------------------------------------------------------------- the cap

def test_cap_leaves_seats_cold_rather_than_arming_rivals():
    r = D(LOPSIDED)
    assert r.seats["A"] == 120 and r.cold == 73
    # the hoarder is still the largest fire -- nobody is elevated past it
    assert max(r.seats.values()) == r.seats["A"]


def test_hoarding_cannot_reach_a_majority():
    r = D(LOPSIDED)
    assert not r.can_pass(["A"])


def test_dividing_claims_the_cold_seats():
    whole = D(LOPSIDED)
    split = D(divide(LOPSIDED, "A", {"A1": 0.5, "A2": 0.5}))
    assert seats_of(split, "A") > whole.seats["A"] + 80   # 211 vs 120
    assert split.cold == 0 and whole.cold == 73


def test_small_parties_are_not_pushed_to_divide():
    """The cliff, not a rule, stops fragmentation at the bottom."""
    split = D(divide(LOPSIDED, "C", {"C1": 0.5, "C2": 0.5}))
    assert seats_of(split, "C") == 0


# ------------------------------------------------------- the dividing ladder

def test_dividing_ladder():
    """Divide once and you govern. Divide three times and you own the state.

    Two thirds of the chamber is what stops the second case; the cliff --
    tested below -- is what stops a four-way division.
    """
    ladder = {}
    for n in (1, 2, 3, 4):
        v = divide(LOPSIDED, "A", {f"A{i+1}": 1 / n for i in range(n)}) \
            if n > 1 else dict(LOPSIDED)
        r = D(v)
        ladder[n] = (fires_held(r, "A"), seats_of(r, "A"),
                     r.can_act([p for p in r.seats if p.startswith("A")]))

    assert ladder[1][:2] == (1, 120)          # whole: one fire, capped
    assert ladder[2][0] == 2                  # divided once: two fires
    assert abs(ladder[2][1] - 210) <= 1       # ...and a majority. The shards
    assert ladder[3][:2] == (3, 235)          # tie with B at 20%, so the last
    assert ladder[4][:2] == (4, 267)          # seat falls arbitrarily.
    assert not ladder[2][2] and not ladder[3][2]   # neither can act alone


def test_three_fires_and_a_bare_majority_are_not_enough():
    """The reason the seat key is a supermajority."""
    v = divide(LOPSIDED, "A", {"A1": 1 / 3, "A2": 1 / 3, "A3": 1 / 3})
    r = D(v)
    shards = [p for p in r.seats if p.startswith("A")]
    assert r.council_votes(shards) >= r.fires_required
    assert r.can_pass(shards)          # holds the chamber
    assert not r.can_act(shards)       # cannot touch the constitution


def test_over_division_runs_out_of_cushion():
    """A four-way division does clear both keys -- and sits 2 points off
    the cliff, where losing one shard costs a fire and its seats."""
    v = divide(LOPSIDED, "A", {f"A{i+1}": 0.25 for i in range(4)})
    r = D(v)
    shards = [p for p in r.seats if p.startswith("A")]
    assert r.can_act(shards)
    sixth = sorted(v.values(), reverse=True)[5]
    assert min(v[p] for p in shards) - sixth < 2.5

    # and it is a real risk: one shard slipping below the cliff is ruinous
    slipped = dict(v, A4=7.5)
    assert seats_of(D(slipped), "A") < seats_of(r, "A") - 50


# --------------------------------------------------------- the merging ladder

def test_the_tail_can_organise_its_way_in():
    """24% of the electorate goes from mostly wasted to the second fire."""
    r = D(LOPSIDED)
    assert set(r.ejected) >= {"T2", "T3", "T4"}
    joined = D(merge(LOPSIDED, ["T1", "T2", "T3", "T4"], name="T"))
    assert joined.fires[1].name == "T"           # second only to A
    assert joined.seats["T"] > r.seats["T1"]
    assert r.wasted > 15 and joined.wasted < 2


def test_merging_back_is_punished_by_the_cap():
    split = D(divide(LOPSIDED, "A", {"A1": 0.5, "A2": 0.5}))
    back = D(LOPSIDED)
    assert back.seats["A"] < seats_of(split, "A") - 80
    assert back.cold > 0 and split.cold == 0


def test_absorption_stops_dead_at_the_cap():
    split = divide(LOPSIDED, "A", {"A1": 0.5, "A2": 0.5})
    at_cap = D(merge(split, ["A1", "C"], name="M")).seats["M"]
    past_cap = D(merge(split, ["A1", "C", "T1"], name="M")).seats["M"]
    assert at_cap == past_cap           # eating more buys literally nothing


def test_absorption_does_not_empty_a_council_seat():
    split = divide(LOPSIDED, "A", {"A1": 0.5, "A2": 0.5})
    after = D(merge(split, ["A1", "C"], name="M"))
    assert len(after.fires) == 5        # the vacated fire refills from the tail
    assert after.wasted < D(split).wasted


# ------------------------------------------------------------------- council

def test_council_is_one_voice_per_fire():
    r = D({"A": 30, "B": 25, "C": 20, "D": 20, "E": 5})
    assert len(r.council) == 5
    assert r.council_votes(["E"]) == r.council_votes(["A"]) == 1


def test_dual_key_blocks_minority_capture():
    r = D({"A": 30, "B": 30, "C": 20, "D": 15, "E": 5})
    assert not r.can_act(["C", "D", "E"])
    assert r.can_act(["A", "B", "C"])


def test_council_key_alone_would_have_allowed_it():
    r = replace(D, seat_supermajority=0.5001)({"A": 30, "B": 30, "C": 20,
                                               "D": 15, "E": 5})
    assert r.can_act(["A", "B"]) is False       # two fires, three required
    assert r.can_act(["A", "B", "E"])           # bare majority would pass


def test_coalitions_are_minimal():
    r = D({"A": 30, "B": 25, "C": 20, "D": 20, "E": 5})
    cs = r.coalitions(r.can_act)
    assert all(r.can_act(c) for c in cs)
    assert not any(set(a) < set(b) for a in cs for b in cs)


# ------------------------------------------------------- post-count rescue

def test_rescue_is_gated_by_the_rule():
    """Whether the shipped config enables it is a policy choice; that the
    gate holds when it is switched off is not."""
    off = replace(D, rescue=False)
    try:
        off(LOPSIDED, rescue=[["T2", "T3"]])
    except ValueError as e:
        assert "rescue is off" in str(e)
    else:
        raise AssertionError("rescue should be refused when disabled")


def test_rescue_lowers_the_wasted_vote():
    d = replace(D, rescue=True, rescue_floor=0.0)   # E holds 1%
    base = d(LOPSIDED)
    saved = d(LOPSIDED, rescue=[["T2", "T3", "T4", "E"]])
    assert saved.wasted < base.wasted
    assert saved.rescued == (("T2", "T3", "T4", "E"),)
    fire = saved.fire_of("T3")
    assert fire is not None and set(fire.parties) == {"T2", "T3", "T4", "E"}


def test_the_floor_applies_to_joiners_too():
    """A host cannot carry a party in under the floor with it."""
    d = replace(D, rescue=True, rescue_floor=0.02)
    try:
        d(LOPSIDED, rescue=[["C", "E"]])            # E holds 1%
    except ValueError as e:
        assert "rescue floor" in str(e)
    else:
        raise AssertionError("the floor must bind joiners as well as mergers")


def test_rescue_always_displaces_a_seated_party():
    """Not a risk -- an identity. There are five fires; a rescue that claims
    one necessarily unseats a party that won one on the night. A rescue is
    never additive, it is a transfer."""
    d = replace(D, rescue=True, rescue_floor=0.0)
    base = d(LOPSIDED)
    saved = d(LOPSIDED, rescue=[["T2", "T3", "T4", "E"]])
    assert saved.fire_of("T2") is not None            # the rescue won a fire
    assert set(saved.ejected) - set(base.ejected) == {"D"}
    assert len(saved.fires) == len(base.fires) == 5


def test_rescue_floor_excludes_the_dust():
    d = replace(D, rescue=True, rescue_floor=0.02)
    assert "E" not in d.eligible(LOPSIDED)            # E holds 1%
    assert {"T2", "T3", "T4"} <= set(d.eligible(LOPSIDED))
    try:
        d(LOPSIDED, rescue=[["E", "T2"]])
    except ValueError as e:
        assert "rescue floor" in str(e)
    else:
        raise AssertionError("a party below the floor must not join a rescue")


def test_rescue_floor_trades_representation_for_stability():
    """Raising the floor leaves more vote wasted but unseats fewer winners."""
    low = replace(D, rescue=True, rescue_floor=0.0)
    high = replace(D, rescue=True, rescue_floor=0.05)
    assert len(high.eligible(LOPSIDED)) < len(low.eligible(LOPSIDED))
    w_low = low(LOPSIDED, rescue=[list(low.eligible(LOPSIDED))]).wasted
    w_high = high(LOPSIDED, rescue=[list(high.eligible(LOPSIDED))]).wasted
    assert w_low < w_high


def test_viable_rescues_are_minimal_and_would_win():
    d = replace(D, rescue=True)
    groups = d.viable_rescues(LOPSIDED)
    assert groups and all(len(g) >= 2 for g in groups)
    for g in groups:
        assert d(LOPSIDED, rescue=[list(g)]).fire_of(g[0]) is not None
    assert not any(set(a) < set(b) for a in groups for b in groups)


def test_a_rescue_may_join_a_fire_already_tended():
    """Joining is additive: nobody is unseated and the fire count holds."""
    d = replace(D, rescue=True, rescue_floor=0.02)
    base = d(LOPSIDED)
    joined = d(LOPSIDED, rescue=[["C", "T2", "T3", "T4"]])
    assert set(joined.ejected) == set(base.ejected) - {"T2", "T3", "T4"}
    assert joined.fire_of("T2") is joined.fire_of("C")
    assert joined.seats["C+T2+T3+T4"] > base.seats["C"]
    assert joined.wasted < base.wasted - 10


def test_a_full_fire_takes_no_more_fuel():
    """A fire at the cap gains nothing by hosting, so it could outbid every
    other host for free and burn what it took."""
    d = replace(D, rescue=True, rescue_floor=0.02)
    assert d(LOPSIDED).seats["A"] == 120                # A sits at the cap
    try:
        d(LOPSIDED, rescue=[["A", "T2"]])
    except ValueError as e:
        assert "no room to host" in str(e)
    else:
        raise AssertionError("a capped fire must not host a rescue")


def test_a_rescue_may_not_merge_two_fires():
    d = replace(D, rescue=True, rescue_floor=0.02)
    try:
        d(LOPSIDED, rescue=[["C", "T1", "T2"]])
    except ValueError as e:
        assert "all tend fires" in str(e)
    else:
        raise AssertionError("two seated fires must not merge after the count")


def test_joining_beats_merging_on_both_counts():
    """The tail's real choice: seats without a voice, or a voice that costs
    a seated party its fire."""
    d = replace(D, rescue=True, rescue_floor=0.02)
    tail = ["T2", "T3", "T4"]
    join = d(LOPSIDED, rescue=[["C", *tail]])
    own = d(LOPSIDED, rescue=[tail])
    assert join.wasted < own.wasted                     # less vote wasted
    assert not set(own.ejected) <= set(d(LOPSIDED).ejected)   # ...but D falls
    assert len(own.fire_of("T2").parties) == 3          # they hold a fire
    assert "C" in join.fire_of("T2").parties            # they hold a share


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
