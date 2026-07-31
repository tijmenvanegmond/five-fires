"""
The dual-majority guarantee, generalised.

For N fires, a structural act needs ceil(0.6 * N) of them plus >50% of the
weight, in BOTH chambers. Question: does the pigeonhole guarantee hold at
every N, and where is it thinnest?
"""

import random
from itertools import combinations
from math import ceil, comb, exp


def required(n):
    return ceil(0.6 * n)


def coalitions(n):
    return list(combinations(range(n), required(n)))


def viable(weights, n):
    k = required(n)
    return [c for c in combinations(range(n), k)
            if sum(weights[i] for i in c) > 50]


def weights(rng, n, skew=2):
    raw = [rng.random() ** skew for _ in range(n)]
    return [100 * r / sum(raw) for r in raw]


def two_chambers(rng, n, divergence, skew=2):
    house = weights(rng, n, skew)
    bent = [h * exp(divergence * rng.gauss(0, 1)) for h in house]
    return house, [100 * b / sum(bent) for b in bent]


def shared(house, senate, n):
    k = required(n)
    return [c for c in combinations(range(n), k)
            if sum(house[i] for i in c) > 50 and sum(senate[i] for i in c) > 50]


def theoretical_max_failures(n):
    """
    A coalition of k fires fails iff the excluded (n-k) fires hold >= 50%.
    Worst case is one fire holding a majority alone: then every excluded-set
    containing it fails. Count those.
    """
    k = required(n)
    excluded = n - k
    if excluded == 0:
        return 0
    # excluded-sets that contain the dominant fire
    return comb(n - 1, excluded - 1)


# ------------------------------------------------------------------- report

TRIALS = 200_000

if __name__ == "__main__":
    print("=" * 74)
    print("DUAL-MAJORITY GUARANTEE ACROSS FIRE COUNTS")
    print("=" * 74)

    print(f"\n{'fires':>6}{'needed':>8}{'coalitions':>12}{'max fail':>10}"
          f"{'min viable':>12}{'pigeonhole':>12}{'margin':>9}")
    print("-" * 74)
    rows = []
    for n in range(3, 8):
        k = required(n)
        total = comb(n, k)
        maxfail = theoretical_max_failures(n)
        minviable = total - maxfail
        ok = 2 * minviable > total
        margin = 2 * minviable / total
        rows.append((n, margin))
        print(f"{n:>6}{k:>8}{total:>12}{maxfail:>10}{minviable:>12}"
              f"{'holds' if ok else 'FAILS':>12}{margin:>9.2f}")

    print("\n  margin = 2 x min_viable / total_coalitions; must exceed 1.00")
    tight = min(rows, key=lambda r: r[1])
    print(f"  thinnest guarantee: {tight[0]} fires at {tight[1]:.2f}")

    # ---------------------------------------------------------- empirical
    print("\n" + "=" * 74)
    print(f"EMPIRICAL — {TRIALS:,} two-chamber elections per cell")
    print("=" * 74)
    print(f"\n{'fires':>6}  " + "".join(f"{d:>10.1f}" for d in
          (0.0, 0.5, 1.0, 2.0, 3.0)) + "     <- chamber divergence")
    print(f"{'':>6}  " + "".join(f"{'routes':>10}" for _ in range(5)))
    print("-" * 74)

    deadlocks = {}
    for n in range(3, 8):
        cells = []
        for d in (0.0, 0.5, 1.0, 2.0, 3.0):
            rng = random.Random(11)
            counts = [len(shared(*two_chambers(rng, n, d), n))
                      for _ in range(TRIALS)]
            dead = sum(c == 0 for c in counts)
            deadlocks[(n, d)] = dead
            cells.append(f"{min(counts):>4}/{sum(counts)/len(counts):<5.1f}")
        print(f"{n:>6}  " + "".join(f"{c:>10}" for c in cells))

    print("\n  shown as  min/mean  viable minimal coalitions")
    total_dead = sum(deadlocks.values())
    print(f"  deadlocks across all {len(deadlocks) * TRIALS:,} elections: {total_dead}")

    # ------------------------------------------------- lockout & fluidity
    print("\n" + "=" * 74)
    print("FLUIDITY — can any fire be permanently frozen out?")
    print("=" * 74)
    print(f"\n{'fires':>6}{'coalitions':>12}{'mean routes':>14}"
          f"{'a fire locked out':>20}{'mean share needed':>20}")
    print("-" * 74)

    for n in range(3, 8):
        rng = random.Random(23)
        lockouts = 0
        routes = []
        cost = []
        for _ in range(TRIALS // 4):
            h, s = two_chambers(rng, n, 0.5)
            v = shared(h, s, n)
            routes.append(len(v))
            if v:
                present = {i for c in v for i in c}
                if len(present) < n:
                    lockouts += 1
                cheapest = min(v, key=lambda c: sum(h[i] for i in c))
                cost.append(sum(h[i] for i in cheapest))
        m = TRIALS // 4
        print(f"{n:>6}{comb(n, required(n)):>12}{sum(routes)/m:>14.2f}"
              f"{100*lockouts/m:>19.2f}%{sum(cost)/len(cost):>19.1f}%")

    print("\n  'a fire locked out' = elections where some fire appears in no")
    print("  viable coalition at all, and thus cannot join any government.")
