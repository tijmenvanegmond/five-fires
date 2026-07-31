"""
Emit the worked scenarios as JSON — the cases the manifesto argues from.

    python scenarios.py > scenarios.json
    python scenarios.py --pretty

Every number quoted in README.md and manifesto.md comes from here, so the
prose and the data cannot drift apart without this file changing.
"""

from __future__ import annotations

import json
from dataclasses import replace

from distributor import Distributor, divide, merge

D = Distributor.from_yaml("config.yaml")

# One dominant party, one mid, a long tail. The case the design exists for.
LOPSIDED = {"A": 40, "B": 20, "C": 8, "D": 7, "E": 1,
            "T1": 8, "T2": 7, "T3": 5, "T4": 4}

ELECTORATES = {
    "lopsided": LOPSIDED,
    "duopoly": {"A": 45, "B": 38, "C": 5, "D": 4, "E": 3, "F": 2, "G": 2, "H": 1},
    "healthy": {"A": 24, "B": 22, "C": 20, "D": 18, "E": 12, "F": 3, "G": 1},
    "fragmented": {"A": 22, "B": 18, "C": 12, "D": 10, "E": 9,
                   "F": 8, "G": 7, "H": 6, "I": 5, "J": 3},
}


def bloc(alloc, prefix):
    return {
        "fires": sum(1 for f in alloc.fires if f.name.startswith(prefix)),
        "seats": sum(s for p, s in alloc.seats.items() if p.startswith(prefix)),
    }


def dividing_ladder(d=D, votes=LOPSIDED, party="A"):
    """What a 40% party gets for dividing 1, 2, 3, 4 ways."""
    out = []
    for n in (1, 2, 3, 4):
        v = dict(votes) if n == 1 else divide(
            votes, party, {f"{party}{i+1}": 1 / n for i in range(n)}
        )
        r = d(v)
        shards = [p for p in r.seats if p.startswith(party)]
        sixth = sorted(v.values(), reverse=True)[5]
        out.append({
            "ways": n,
            **bloc(r, party),
            "cold": r.cold,
            "can_pass": r.can_pass(shards),
            "can_act": r.can_act(shards),
            "cushion_over_sixth": round(min(v[p] for p in shards) - sixth, 2),
            "allocation": r.to_dict(),
        })
    return out


def merging_ladder(d=D, votes=LOPSIDED):
    """What the tail gets for combining, one party at a time."""
    tail = ["T1", "T2", "T3", "T4"]
    out = []
    for n in range(1, len(tail) + 1):
        group = tail[:n]
        v = votes if n == 1 else merge(votes, group, name="T")
        r = d(v)
        name = group[0] if n == 1 else "T"
        out.append({
            "parties_merged": n,
            "combined_vote": round(sum(votes[p] for p in group), 2),
            "seats": r.seats.get(name, 0),
            "holds_a_fire": r.fire_of(name) is not None,
            "wasted_vote": round(r.wasted, 2),
            "allocation": r.to_dict(),
        })
    return out


def absorption_ladder(d=D, votes=LOPSIDED):
    """A fire eating smaller parties — and where that stops paying."""
    split = divide(votes, "A", {"A1": 0.5, "A2": 0.5})
    out = [{"absorbed": [], "seats": d(split).seats["A1"], "cold": d(split).cold}]
    for eaten in (["C"], ["C", "T1"], ["C", "T1", "D"]):
        r = d(merge(split, ["A1", *eaten], name="M"))
        out.append({
            "absorbed": eaten,
            "seats": r.seats["M"],
            "cold": r.cold,
            "at_cap": r.fire_of("M").cold > 0,
        })
    return out


def rescue_options(d=D, votes=LOPSIDED):
    """Merging with each other vs joining a fire already tended."""
    on = replace(d, rescue=True)
    base = on(votes)
    tail = list(on.eligible(votes))
    rows = [{
        "option": "none",
        "wasted_vote": round(base.wasted, 2),
        "unseated": [],
        "tail_holds_a_council_seat": False,
        "allocation": base.to_dict(),
    }]

    own = on(votes, rescue=[tail])
    rows.append({
        "option": "tail takes its own fire",
        "wasted_vote": round(own.wasted, 2),
        "unseated": sorted(set(own.ejected) - set(base.ejected)),
        "tail_holds_a_council_seat": True,
        "allocation": own.to_dict(),
    })

    for host in [f.name for f in base.fires]:
        try:
            r = on(votes, rescue=[[host, *tail]])
        except ValueError as e:
            rows.append({"option": f"tail joins {host}", "refused": str(e)})
            continue
        rows.append({
            "option": f"tail joins {host}",
            "wasted_vote": round(r.wasted, 2),
            "unseated": sorted(set(r.ejected) - set(base.ejected)),
            "tail_holds_a_council_seat": False,
            "host_seats_before": base.seats[host],
            "host_seats_after": r.seats[r.fire_of(host).name],
            "allocation": r.to_dict(),
        })
    return rows


def rescue_floor_sweep(d=D, votes=LOPSIDED):
    """What the participation floor buys and what it costs."""
    out = []
    for floor in (0.0, 0.01, 0.02, 0.05, 0.08):
        on = replace(d, rescue=True, rescue_floor=floor)
        elig = list(on.eligible(votes))
        row = {"floor": floor, "eligible": elig}
        if len(elig) >= 2:
            r = on(votes, rescue=[elig])
            row |= {
                "wasted_vote": round(r.wasted, 2),
                "claims_a_fire": r.fire_of(elig[0]) is not None,
                "unseated": sorted(set(r.ejected) - set(on(votes).ejected)),
            }
        else:
            row |= {"wasted_vote": round(on(votes).wasted, 2),
                    "claims_a_fire": False, "unseated": []}
        out.append(row)
    return out


def divisor_check():
    """The corrected claim: no divisor rewards dividing."""
    whole = {"A": 40, "B": 20, "C": 20, "D": 15, "E": 5}
    split = divide(whole, "A", {"A1": 0.5, "A2": 0.5})
    out = {}
    for div in ("sainte_lague", "dhondt"):
        d = replace(D, divisor=div, cap=None, fires=6)
        out[div] = {
            "whole": d(whole).seats["A"],
            "divided": bloc(d(split), "A")["seats"],
        }
        out[div]["delta"] = out[div]["divided"] - out[div]["whole"]
    return out


def build():
    return {
        "config": {
            "fires": D.fires,
            "seats": D.seats,
            "divisor": D.divisor,
            "cap": D.cap,
            "rescue": D.rescue,
            "rescue_floor": D.rescue_floor,
            "structural_fires": D.structural_fires,
            "seat_supermajority": D.seat_supermajority,
        },
        "electorates": ELECTORATES,
        "dividing_ladder": dividing_ladder(),
        "merging_ladder": merging_ladder(),
        "absorption_ladder": absorption_ladder(),
        "rescue_options": rescue_options(),
        "rescue_floor_sweep": rescue_floor_sweep(),
        "divisor_check": divisor_check(),
        "by_electorate": {
            name: replace(D, rescue=True)(v).to_dict()
            for name, v in ELECTORATES.items()
        },
    }


if __name__ == "__main__":
    import sys
    pretty = "--pretty" in sys.argv
    print(json.dumps(build(), indent=2 if pretty else None))
