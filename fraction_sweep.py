"""
Is the population cost of a minimal coalition a property of the FRACTION
of fires required, or of the NUMBER of fires?

Previous run coupled them: fraction was fixed at 0.6 and only N varied.
Here k (fires required) is swept independently of N, so every (N, k) pair
is measured on its own terms.

If cost is determined by k/N alone, all points collapse onto one curve and
the earlier 60.1% figure is just the fraction reflected back.
If cost separates by N at matched fraction, the fire count does real work.
"""

import random
from itertools import combinations
from math import exp

TRIALS = 60_000
DIVERGENCE = 0.5


def two_chambers(rng, n, divergence=DIVERGENCE, skew=2):
    raw = [rng.random() ** skew for _ in range(n)]
    house = [100 * r / sum(raw) for r in raw]
    bent = [h * exp(divergence * rng.gauss(0, 1)) for h in house]
    return house, [100 * b / sum(bent) for b in bent]


def measure(n, k, trials=TRIALS, seed=31):
    """Mean population cost of the cheapest viable k-fire coalition."""
    rng = random.Random(seed)
    costs, routes, dead = [], [], 0
    for _ in range(trials):
        h, s = two_chambers(rng, n)
        v = [c for c in combinations(range(n), k)
             if sum(h[i] for i in c) > 50 and sum(s[i] for i in c) > 50]
        routes.append(len(v))
        if not v:
            dead += 1
        else:
            costs.append(min(sum(h[i] for i in c) for c in v))
    return {
        "cost": sum(costs) / len(costs) if costs else float("nan"),
        "routes": sum(routes) / len(routes),
        "deadlock": 100 * dead / trials,
    }


if __name__ == "__main__":
    print("=" * 78)
    print("POPULATION COST OF A MINIMAL COALITION — k SWEPT INDEPENDENTLY OF N")
    print("=" * 78)

    grid = {}
    print(f"\n{'':>7}" + "".join(f"{'k=' + str(k):>11}" for k in range(2, 8)))
    print("-" * 78)
    for n in range(3, 8):
        row = ""
        for k in range(2, 8):
            if k > n:
                row += f"{'':>11}"
                continue
            r = measure(n, k)
            grid[(n, k)] = r
            row += f"{r['cost']:>10.1f}%"
        print(f"  N={n:<3}" + row)
    print("\n  cells: mean share of the population held by the cheapest")
    print("  coalition that clears both chambers")

    # ---- the decisive test: do points collapse onto one curve?
    print("\n" + "=" * 78)
    print("COST AGAINST EFFECTIVE FRACTION  (k/N)")
    print("=" * 78)
    print(f"\n{'k/N':>7}{'N':>5}{'k':>4}{'cost':>10}{'routes':>9}{'deadlock':>10}")
    print("-" * 78)
    for (n, k), r in sorted(grid.items(), key=lambda kv: kv[0][1] / kv[0][0]):
        print(f"{k/n:>7.2f}{n:>5}{k:>4}{r['cost']:>9.1f}%"
              f"{r['routes']:>9.2f}{r['deadlock']:>9.2f}%")

    # ---- matched-fraction comparison
    print("\n" + "=" * 78)
    print("MATCHED FRACTIONS — does N still matter when k/N is held fixed?")
    print("=" * 78)
    bands = {
        "~0.50": [(4, 2), (6, 3)],
        "~0.67": [(3, 2), (6, 4)],
        "~0.71-0.75": [(4, 3), (7, 5)],
        "~0.80": [(5, 4)],
    }
    for label, pairs in bands.items():
        vals = [(n, k, grid[(n, k)]) for n, k in pairs if (n, k) in grid]
        if len(vals) < 2:
            continue
        print(f"\n  fraction {label}")
        for n, k, r in vals:
            print(f"    N={n} k={k}   cost {r['cost']:.1f}%   "
                  f"routes {r['routes']:.2f}")
        spread = max(v[2]["cost"] for v in vals) - min(v[2]["cost"] for v in vals)
        print(f"    spread in cost at matched fraction: {spread:.1f} points")

    # ---- what the manifesto rule actually picks out
    print("\n" + "=" * 78)
    print("THE CONFIGURED RULE  (ceil(0.6 x N))")
    print("=" * 78)
    from math import ceil
    print(f"\n{'N':>4}{'k':>4}{'k/N':>8}{'cost':>10}{'routes':>9}")
    print("-" * 78)
    for n in range(3, 8):
        k = ceil(0.6 * n)
        r = grid[(n, k)]
        print(f"{n:>4}{k:>4}{k/n:>8.2f}{r['cost']:>9.1f}%{r['routes']:>9.2f}")
