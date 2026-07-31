"""
Five Fires — round two.

Round one found three problems. This tests the fixes.
"""

import random
from itertools import combinations
from fivefires import Party, sainte_lague, PROPORTIONAL_SEATS, TOTAL_SEATS, random_distribution

BONUS_POOL = [11, 9, 7, 5, 3]


def allocate_v2(parties, bonus_per_fire=True):
    """
    v2: bonus seats are allocated PER FIRE, not per party.
    A fire containing two parties splits one bonus allocation between them.
    """
    for p in parties:
        p.seats = p.bonus = 0
        p.recognized = False

    groups = {}
    for p in parties:
        groups.setdefault(p.lineage, []).append(p)
    ranked = sorted(groups.values(), key=lambda g: -sum(x.votes for x in g))
    fires = ranked[:5]

    rec = [p for g in fires for p in g]
    for p in rec:
        p.recognized = True

    seats = sainte_lague([p.votes for p in rec], PROPORTIONAL_SEATS)
    for p, s in zip(rec, seats):
        p.seats = s

    if bonus_per_fire:
        # rank FIRES by combined proportional seats, smallest fire gets most
        by_size = sorted(fires, key=lambda g: sum(p.seats for p in g))
        for g, b in zip(by_size, BONUS_POOL):
            # split the fire's bonus among its parties, largest remainder
            tot = sum(p.seats for p in g) or 1
            given = 0
            for p in g[:-1]:
                share = round(b * p.seats / tot)
                p.bonus = share
                given += share
            g[-1].bonus = b - given
    else:
        by_size = sorted(rec, key=lambda p: p.seats)
        for p, b in zip(by_size, BONUS_POOL):
            p.bonus = b

    return rec, fires


def split_test_v2(dist, bonus_per_fire):
    base = [Party(chr(65 + i), v) for i, v in enumerate(dist)]
    rec, _ = allocate_v2(base, bonus_per_fire)
    before = base[0].total
    names_before = {p.name for p in rec}

    v = dist[0]
    split = [Party("A1", v * 0.52, lineage="A"), Party("A2", v * 0.48, lineage="A")]
    split += [Party(chr(66 + i), x) for i, x in enumerate(dist[1:])]
    rec2, _ = allocate_v2(split, bonus_per_fire)
    after = sum(p.total for p in split if p.lineage == "A")
    ejected = {n for n in names_before if n != "A"} - {p.name for p in rec2}
    return after - before, sorted(ejected)


def inversion_rate(bonus, trials=20000, seed=3):
    """How often does the bonus reorder parties against the popular vote?"""
    global BONUS_POOL
    old, BONUS_POOL = BONUS_POOL, bonus
    rng = random.Random(seed)
    inv = 0
    for _ in range(trials):
        d = random_distribution(5, rng)
        ps = [Party(chr(65 + i), v) for i, v in enumerate(d)]
        rec, _ = allocate_v2(ps)
        a = [p.name for p in sorted(rec, key=lambda x: -x.seats)]
        b = [p.name for p in sorted(rec, key=lambda x: -x.total)]
        if a != b:
            inv += 1
    BONUS_POOL = old
    return 100 * inv / trials


if __name__ == "__main__":
    print("=" * 62)
    print("ROUND TWO — TESTING THE FIXES")
    print("=" * 62)

    print("\nFIX 1  bonus allocated per FIRE rather than per PARTY")
    print("       (does splitting still pay?)")
    rng = random.Random(11)
    for per_fire in (False, True):
        gains = ejects = 0
        for _ in range(5000):
            d = random_distribution(6, rng)
            g, e = split_test_v2(d, per_fire)
            if g > 0:
                gains += 1
            if e:
                ejects += 1
        tag = "bonus per FIRE " if per_fire else "bonus per PARTY"
        print(f"  {tag}: splitting gains seats {100*gains/5000:5.1f}% of the time,"
              f"  ejects a rival {100*ejects/5000:.1f}%")

    print("\nFIX 2  bonus curve shape vs. vote-order inversions")
    print("       (how often does the bonus put a smaller party above a larger one?)")
    curves = {
        "11/9/7/5/3  (steps of 2)": [11, 9, 7, 5, 3],
        "13/9/7/4/2  (steeper)   ": [13, 9, 7, 4, 2],
        "15/10/6/3/1 (steepest)  ": [15, 10, 6, 3, 1],
        "9/8/7/6/5   (flattest)  ": [9, 8, 7, 6, 5],
        "35/0/0/0/0  (floor only)": [35, 0, 0, 0, 0],
    }
    for label, curve in curves.items():
        print(f"  {label}: {inversion_rate(curve):5.2f}% of elections reordered")

    print("\nFIX 3  what the bonus actually buys the smallest fire")
    for d in ([33, 33, 11, 11, 11], [40, 25, 20, 10, 5], [30, 28, 20, 18, 4]):
        ps = [Party(chr(65 + i), v) for i, v in enumerate(d)]
        rec, _ = allocate_v2(ps)
        s = min(rec, key=lambda p: p.total)
        raw = 100 * s.seats / TOTAL_SEATS
        boosted = 100 * s.total / TOTAL_SEATS
        print(f"  {str(d):<22} smallest fire: {raw:.1f}% -> {boosted:.1f}% "
              f"(+{boosted-raw:.1f}pt)")
