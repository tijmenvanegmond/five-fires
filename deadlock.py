"""
Five seats, one person each, weighted by the population behind them.

A decision needs a DUAL MAJORITY:
    - at least 3 of the 5 fires, and
    - more than 50% of the weight

...and must clear that bar in BOTH chambers simultaneously.

Result: deadlock is impossible. Not rare — impossible. Proof below,
confirmed by simulation across extreme chamber divergence.
"""

import random
from itertools import combinations
from math import exp

FIRES = 5
TRIPLES = list(combinations(range(FIRES), 3))   # 10 of them

PROOF = """
WHY DUAL-MAJORITY DEADLOCK CANNOT HAPPEN

  A 3-fire coalition fails only if the excluded pair holds >= 50%.
  So failing triples correspond one-to-one with pairs at >= 50%.

  How many pairs can reach 50%?
    - if some fire holds > 50% alone, every pair containing it qualifies: 4
    - otherwise only pairs drawn from the top three qualify:            3
  So at most 4 triples fail, and at least 6 of the 10 always clear.

  Each chamber independently admits >= 6 of the SAME 10 triples.
  6 + 6 = 12 > 10, so by pigeonhole the two chambers share >= 2.

  Some minimal coalition can always act, however far the chambers diverge.
  The dual majority is demanding, but it is not a deadlock machine.
"""


def viable(weights, n=3):
    return [c for c in combinations(range(FIRES), n)
            if sum(weights[i] for i in c) > 50]


def shared(house, senate):
    return [c for c in TRIPLES
            if sum(house[i] for i in c) > 50 and sum(senate[i] for i in c) > 50]


def chambers(rng, divergence):
    """House tracks the national vote; the Senate bends it by `divergence`."""
    raw = [rng.random() ** 2 for _ in range(FIRES)]
    house = [100 * r / sum(raw) for r in raw]
    bent = [h * exp(divergence * rng.gauss(0, 1)) for h in house]
    return house, [100 * b / sum(bent) for b in bent]


if __name__ == "__main__":
    print("=" * 66)
    print("FIVE WEIGHTED SEATS — DEADLOCK UNDER DUAL MAJORITY")
    print("=" * 66)

    rng = random.Random(5)
    worst = 0
    for _ in range(200_000):
        raw = [rng.random() ** 3 for _ in range(FIRES)]
        w = [100 * r / sum(raw) for r in raw]
        worst = max(worst, 10 - len(viable(w)))
    print(f"\nONE CHAMBER  (200,000 distributions)")
    print(f"  most triples that ever failed : {worst} of 10")
    print(f"  fewest that ever worked       : {10 - worst} of 10")

    print("\nTWO CHAMBERS  (200,000 distributions each)")
    print(f"  {'divergence':>11}{'deadlock':>11}{'min routes':>12}{'avg routes':>12}")
    for d in (0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
        rng = random.Random(4)
        counts = [len(shared(*chambers(rng, d))) for _ in range(200_000)]
        dead = 100 * sum(c == 0 for c in counts) / len(counts)
        tag = {0.0: "identical", 3.0: "unrecognisable"}.get(d, "")
        print(f"  {d:>11.2f}{dead:>10.2f}%{min(counts):>12}"
              f"{sum(counts)/len(counts):>12.2f}   {tag}")

    print(PROOF)
