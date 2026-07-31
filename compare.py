"""
Same electorate, different number of fires.

Holds everything constant except recognition count, so any difference in
the output is attributable to the fire count and nothing else.
"""

from dataclasses import replace
from itertools import combinations
from math import sqrt

from distributor import Distributor

# A plausibly fractured American electorate (national vote share).
ELECTORATE = {
    "Common Ground":   24.0,
    "Heartland":       23.0,
    "Labor Union":     21.0,
    "New Federalists": 16.0,
    "Roots":           11.0,
    "Liberty":          5.0,
}


# ------------------------------------------------------------------- metrics

def gallagher(votes, alloc):
    """Least-squares disproportionality. 0 = perfect, >5 is considered poor."""
    total = sum(votes.values())
    return sqrt(0.5 * sum(
        (100 * v / total - alloc.share(p)) ** 2 for p, v in votes.items()
    ))


def effective_parties(alloc):
    """Laakso-Taagepera index: how many parties the chamber behaves like."""
    return 1 / sum((alloc.share(p) / 100) ** 2 for p in alloc.seats)


def represented(votes, alloc):
    """Share of the electorate whose chosen party actually holds seats."""
    total = sum(votes.values())
    return 100 * sum(v for p, v in votes.items() if p in alloc.seats) / total


def winning_coalitions(alloc):
    """Minimal party-sets holding a seat majority (ordinary legislation)."""
    return alloc.coalitions(alloc.can_pass)


def solo_majority(alloc):
    return next((p for p, s in alloc.seats.items() if s * 2 > alloc.chamber), None)


# -------------------------------------------------------------------- report

def run(label, dist, votes):
    alloc = dist(votes)
    wins = winning_coalitions(alloc)
    solo = solo_majority(alloc)

    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}")
    print(alloc)
    print(f"\n  disproportionality (Gallagher) : {gallagher(votes, alloc):5.2f}")
    print(f"  effective parties              : {effective_parties(alloc):5.2f}")
    print(f"  electorate represented         : {represented(votes, alloc):5.1f}%")
    print(f"  ways to build a majority       : {len(wins)}")
    print(f"  can one party govern alone     : {solo or 'no'}")

    if len(wins) <= 6:
        for c in sorted(wins, key=lambda c: sum(alloc.seats[p] for p in c)):
            seats = sum(alloc.seats[p] for p in c)
            print(f"      {' + '.join(c):<52} {seats}")
    return alloc, wins


if __name__ == "__main__":
    base = Distributor.from_yaml("config.yaml")

    # Both chambers run uncapped, so the ONLY difference between the runs is
    # how many parties are recognized. (A 30% cap is meaningless in a
    # two-fire chamber -- it would leave 40% of the seats cold. The cap is a
    # separate mechanism; its effect is pinned in test_distributor.py.)
    two = replace(base, fires=2, cap=None)
    five = replace(base, fires=5, cap=None)

    print("electorate:")
    for p, v in ELECTORATE.items():
        print(f"  {p:<18}{v:5.1f}%")

    a2, w2 = run("TWO FIRES", two, ELECTORATE)
    a5, w5 = run("FIVE FIRES", five, ELECTORATE)

    print(f"\n{'=' * 60}\nDELTA\n{'=' * 60}")
    print(f"  disproportionality  {gallagher(ELECTORATE, a2):5.2f}"
          f"  ->{gallagher(ELECTORATE, a5):6.2f}")
    print(f"  effective parties   {effective_parties(a2):5.2f}"
          f"  ->{effective_parties(a5):6.2f}")
    print(f"  represented         {represented(ELECTORATE, a2):5.1f}%"
          f"  ->{represented(ELECTORATE, a5):5.1f}%")
    print(f"  majority routes     {len(w2):5d}  ->{len(w5):6d}")

    # Does the two-fire chamber let a minority seize the structure?
    print(f"\n  structural capture check")
    for label, alloc in (("two fires", a2), ("five fires", a5)):
        names = list(alloc.seats)
        bad = [
            c for n in range(1, len(names) + 1)
            for c in combinations(names, n)
            if alloc.can_act(c) and sum(alloc.seats[p] for p in c) * 2 <= alloc.chamber
        ]
        print(f"    {label:<12}: {len(bad)} minority coalitions can act structurally")
