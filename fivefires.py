"""
Five Fires System — mechanical simulator and stress-test harness.

Implements the rules exactly as specified in the manifesto, then sweeps
vote distributions looking for outcomes the designer would reject.

No narrative, no roleplay. Just the rules, run against every case.
"""

from itertools import combinations
from dataclasses import dataclass, field
import random

PROPORTIONAL_SEATS = 400
BONUS_POOL = [11, 9, 7, 5, 3]  # smallest party first; sums to 35
TOTAL_SEATS = PROPORTIONAL_SEATS + sum(BONUS_POOL)  # 435
FIRES = 5


@dataclass
class Party:
    name: str
    votes: float           # national vote share, 0-100
    lineage: str = ""      # shared id for parties split from a common parent
    seats: int = 0
    bonus: int = 0
    recognized: bool = False

    def __post_init__(self):
        if not self.lineage:
            self.lineage = self.name

    @property
    def total(self):
        return self.seats + self.bonus


# ---------------------------------------------------------------- allocation

def sainte_lague(shares, seats):
    """Standard Sainte-Laguë highest-quotient allocation."""
    alloc = [0] * len(shares)
    for _ in range(seats):
        quotients = [s / (2 * a + 1) for s, a in zip(shares, alloc)]
        alloc[quotients.index(max(quotients))] += 1
    return alloc


def recognize(parties, lineage_rule=False):
    """
    Determine the five recognized fires.

    With lineage_rule on, parties sharing a lineage occupy ONE fire between
    them — their combined vote decides whether that fire is recognized.
    """
    if not lineage_rule:
        ranked = sorted(parties, key=lambda p: -p.votes)
        for i, p in enumerate(ranked):
            p.recognized = i < FIRES
        return ranked[:FIRES]

    # group by lineage, rank groups by combined vote
    groups = {}
    for p in parties:
        groups.setdefault(p.lineage, []).append(p)
    ranked_groups = sorted(groups.values(), key=lambda g: -sum(p.votes for p in g))
    recognized = []
    for i, g in enumerate(ranked_groups):
        for p in g:
            p.recognized = i < FIRES
            if i < FIRES:
                recognized.append(p)
    return recognized


def allocate(parties, lineage_rule=False):
    """Run a full seat allocation. Returns the recognized parties."""
    for p in parties:
        p.seats = p.bonus = 0
        p.recognized = False

    rec = recognize(parties, lineage_rule)
    if not rec:
        return []

    # votes for unrecognized parties redistribute proportionally
    shares = [p.votes for p in rec]
    seats = sainte_lague(shares, PROPORTIONAL_SEATS)
    for p, s in zip(rec, seats):
        p.seats = s

    # bonus seats: reverse order of proportional size, smallest gets most
    by_size = sorted(rec, key=lambda p: p.seats)
    for p, b in zip(by_size, BONUS_POOL):
        p.bonus = b

    return rec


# ------------------------------------------------------------- structural vote

def structural_coalitions(rec, dual_key=True):
    """
    Which coalitions can take a structural action (veto override, court
    confirmation, rule change)?

    fires-only  : any 3 of 5 fires
    dual key    : 3 of 5 fires AND >50% of all seats
    """
    out = []
    for size in range(1, len(rec) + 1):
        for combo in combinations(rec, size):
            fires = len(combo)
            seats = sum(p.total for p in combo)
            if fires < 3:
                continue
            if dual_key and seats <= TOTAL_SEATS / 2:
                continue
            out.append((tuple(p.name for p in combo), fires, seats))
    return out


def minority_capture(rec, dual_key):
    """
    Can a coalition holding a MINORITY of seats take structural action?
    This is the failure we're hunting.
    """
    for names, fires, seats in structural_coalitions(rec, dual_key):
        if seats <= TOTAL_SEATS / 2:
            return (names, seats, 100 * seats / TOTAL_SEATS)
    return None


# ----------------------------------------------------------------- exploits

def split_exploit(dist, lineage_rule):
    """
    Take the largest party, split it in two, and see whether the resulting
    bloc gains seats and/or ejects a rival from recognition.
    """
    base = [Party(chr(65 + i), v) for i, v in enumerate(dist)]
    rec_before = allocate(base, lineage_rule)
    before_total = base[0].total
    names_before = {p.name for p in rec_before}

    # split A into A1 (52%) and A2 (48%) of its vote
    v = dist[0]
    split = [Party("A1", v * 0.52, lineage="A"), Party("A2", v * 0.48, lineage="A")]
    split += [Party(chr(66 + i), x) for i, x in enumerate(dist[1:])]
    rec_after = allocate(split, lineage_rule)
    after_total = sum(p.total for p in split if p.lineage == "A")
    names_after = {p.name for p in rec_after}

    ejected = {n for n in names_before if n != "A"} - names_after
    return {
        "before": before_total,
        "after": after_total,
        "gain": after_total - before_total,
        "ejected": sorted(ejected),
    }


# -------------------------------------------------------------------- sweeps

def random_distribution(n=6, rng=None):
    rng = rng or random
    raw = [rng.random() ** 2 for _ in range(n)]
    total = sum(raw)
    return sorted((100 * r / total for r in raw), reverse=True)


def sweep_minority_capture(trials=20000, dual_key=True, seed=7):
    rng = random.Random(seed)
    hits = []
    for _ in range(trials):
        dist = random_distribution(6, rng)
        parties = [Party(chr(65 + i), v) for i, v in enumerate(dist)]
        rec = allocate(parties)
        cap = minority_capture(rec, dual_key)
        if cap:
            hits.append((dist, cap))
    return hits, trials


def sweep_split_exploit(trials=5000, lineage_rule=False, seed=7):
    rng = random.Random(seed)
    gains = 0
    ejections = 0
    for _ in range(trials):
        dist = random_distribution(6, rng)
        r = split_exploit(dist, lineage_rule)
        if r["gain"] > 0:
            gains += 1
        if r["ejected"]:
            ejections += 1
    return gains, ejections, trials


# --------------------------------------------------------------------- report

def show(dist, label, lineage_rule=False):
    parties = [Party(chr(65 + i), v) for i, v in enumerate(dist)]
    rec = allocate(parties, lineage_rule)
    print(f"\n{label}")
    print(f"  votes: {'  '.join(f'{p.name}:{p.votes:.1f}%' for p in parties)}")
    print(f"  {'party':<6}{'prop':>6}{'bonus':>7}{'total':>7}{'share':>8}")
    for p in sorted(rec, key=lambda x: -x.total):
        print(f"  {p.name:<6}{p.seats:>6}{p.bonus:>7}{p.total:>7}"
              f"{100*p.total/TOTAL_SEATS:>7.1f}%")
    unrec = [p.name for p in parties if not p.recognized]
    if unrec:
        print(f"  ejected: {', '.join(unrec)}")
    return rec


if __name__ == "__main__":
    print("=" * 62)
    print("FIVE FIRES — MECHANICAL STRESS TEST")
    print("=" * 62)

    # ---- Case 1: the distribution you flagged
    rec = show([33, 33, 11, 11, 11], "CASE 1  33/33/11/11/11")
    for dual in (False, True):
        cap = minority_capture(rec, dual)
        key = "3 fires + seat majority" if dual else "3 fires only"
        if cap:
            print(f"  [{key}] MINORITY CAPTURE: {cap[0]} "
                  f"= {cap[1]} seats ({cap[2]:.1f}%)")
        else:
            print(f"  [{key}] no minority capture")

    # ---- Case 2: the split exploit
    print("\n" + "=" * 62)
    print("CASE 2  SPLIT EXPLOIT — A(40) B(25) C(20) D(10) E(5)")
    print("=" * 62)
    dist = [40, 25, 20, 10, 5]
    for lr in (False, True):
        r = split_exploit(dist, lr)
        tag = "lineage rule ON " if lr else "lineage rule OFF"
        print(f"  {tag}: bloc {r['before']} -> {r['after']} seats "
              f"(gain {r['gain']:+d})   ejected: {r['ejected'] or 'none'}")

    # ---- Case 3: bonus seat inversion check
    print("\n" + "=" * 62)
    print("CASE 3  DOES THE BONUS EVER INVERT THE ORDER?")
    print("=" * 62)
    rng = random.Random(3)
    inversions = 0
    for _ in range(20000):
        d = random_distribution(5, rng)
        ps = [Party(chr(65 + i), v) for i, v in enumerate(d)]
        rec = allocate(ps)
        prop_order = [p.name for p in sorted(rec, key=lambda x: -x.seats)]
        tot_order = [p.name for p in sorted(rec, key=lambda x: -x.total)]
        if prop_order != tot_order:
            inversions += 1
            if inversions == 1:
                show(d, "  first inversion found:")
    print(f"\n  order inversions: {inversions} / 20000 "
          f"({100*inversions/20000:.2f}%)")

    # ---- Case 4: sweeps
    print("\n" + "=" * 62)
    print("CASE 4  RANDOM SWEEPS")
    print("=" * 62)
    for dual in (False, True):
        hits, n = sweep_minority_capture(20000, dual)
        key = "3 fires + majority" if dual else "3 fires only      "
        print(f"  minority capture [{key}]: {len(hits)}/{n} "
              f"({100*len(hits)/n:.1f}%)")

    for lr in (False, True):
        g, e, n = sweep_split_exploit(5000, lr)
        tag = "lineage ON " if lr else "lineage OFF"
        print(f"  split exploit [{tag}]: seat gain {g}/{n} "
              f"({100*g/n:.1f}%),  rival ejected {e}/{n} ({100*e/n:.1f}%)")
