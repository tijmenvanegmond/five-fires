"""
Five Fires System - Hard-coded for 5 fires with NO bonus seats.

This is a simplified, hard-coded version specifically for 5 fires
with pure proportional allocation (no bonus seats).

Total seats: 435 (all proportional, no bonus)
Fires: exactly 5
"""

from itertools import combinations
from dataclasses import dataclass

# Hard-coded constants for 5 fires, no bonus
FIRES = 5
TOTAL_SEATS = 435


@dataclass
class Party:
    name: str
    votes: float           # national vote share, 0-100
    seats: int = 0
    recognized: bool = False

    @property
    def total(self):
        return self.seats  # No bonus seats, so total = seats


# ---------------------------------------------------------------- allocation

def sainte_lague(shares, seats):
    """Standard Sainte-Laguë highest-quotient allocation."""
    alloc = [0] * len(shares)
    for _ in range(seats):
        quotients = [s / (2 * a + 1) for s, a in zip(shares, alloc)]
        alloc[quotients.index(max(quotients))] += 1
    return alloc


def recognize(parties):
    """
    Determine the five recognized fires.
    Top 5 parties by vote share hold recognition.
    """
    ranked = sorted(parties, key=lambda p: -p.votes)
    for i, p in enumerate(ranked):
        p.recognized = i < FIRES
    return ranked[:FIRES]


def allocate(parties):
    """
    Run a full seat allocation for 5 fires with NO bonus seats.
    Returns the recognized parties.
    """
    for p in parties:
        p.seats = 0
        p.recognized = False

    rec = recognize(parties)
    if not rec:
        return []

    # All seats are proportional - no bonus seats
    shares = [p.votes for p in rec]
    seats = sainte_lague(shares, TOTAL_SEATS)
    for p, s in zip(rec, seats):
        p.seats = s

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


# --------------------------------------------------------------------- report

def show(dist, label):
    parties = [Party(chr(65 + i), v) for i, v in enumerate(dist)]
    rec = allocate(parties)
    print(f"\n{label}")
    print(f"  votes: {'  '.join(f'{p.name}:{p.votes:.1f}%' for p in parties)}")
    print(f"  {'party':<6}{'seats':>6}{'share':>8}")
    for p in sorted(rec, key=lambda x: -x.total):
        print(f"  {p.name:<6}{p.seats:>6}{100*p.total/TOTAL_SEATS:>7.1f}%")
    unrec = [p.name for p in parties if not p.recognized]
    if unrec:
        print(f"  ejected: {', '.join(unrec)}")
    return rec


if __name__ == "__main__":
    print("=" * 62)
    print("FIVE FIRES - HARD-CODED: 5 FIRES, NO BONUS SEATS")
    print("=" * 62)

    # Test case 1: equal distribution
    rec = show([20, 20, 20, 20, 20], "CASE 1  20/20/20/20/20 (equal)")
    for dual in (False, True):
        cap = minority_capture(rec, dual)
        key = "3 fires + seat majority" if dual else "3 fires only"
        if cap:
            print(f"  [{key}] MINORITY CAPTURE: {cap[0]} "
                  f"= {cap[1]} seats ({cap[2]:.1f}%)")
        else:
            print(f"  [{key}] no minority capture")

    # Test case 2: the original problematic distribution
    rec = show([33, 33, 11, 11, 11], "CASE 2  33/33/11/11/11")
    for dual in (False, True):
        cap = minority_capture(rec, dual)
        key = "3 fires + seat majority" if dual else "3 fires only"
        if cap:
            print(f"  [{key}] MINORITY CAPTURE: {cap[0]} "
                  f"= {cap[1]} seats ({cap[2]:.1f}%)")
        else:
            print(f"  [{key}] no minority capture")

    # Test case 3: skewed distribution
    rec = show([40, 25, 20, 10, 5], "CASE 3  40/25/20/10/5")
    for dual in (False, True):
        cap = minority_capture(rec, dual)
        key = "3 fires + seat majority" if dual else "3 fires only"
        if cap:
            print(f"  [{key}] MINORITY CAPTURE: {cap[0]} "
                  f"= {cap[1]} seats ({cap[2]:.1f}%)")
        else:
            print(f"  [{key}] no minority capture")

    # Test case 4: with a 6th party (should be ejected)
    print("\n" + "=" * 62)
    print("CASE 4  WITH 6TH PARTY (should be ejected)")
    print("=" * 62)
    parties = [Party(chr(65 + i), v) for i, v in enumerate([30, 25, 20, 15, 8, 2])]
    rec = allocate(parties)
    print(f"  votes: {'  '.join(f'{p.name}:{p.votes:.1f}%' for p in parties)}")
    print(f"  {'party':<6}{'seats':>6}{'share':>8}")
    for p in sorted(rec, key=lambda x: -x.total):
        print(f"  {p.name:<6}{p.seats:>6}{100*p.total/TOTAL_SEATS:>7.1f}%")
    unrec = [p.name for p in parties if not p.recognized]
    print(f"  ejected: {', '.join(unrec)}")
    print(f"  Total seats allocated: {sum(p.seats for p in rec)} (should be {TOTAL_SEATS})")
