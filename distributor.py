"""
Five Fires — seat distributor.

    from distributor import Distributor

    d = Distributor.from_yaml("config.yaml")
    r = d({"A": 33, "B": 33, "C": 11, "D": 11, "E": 11})

    r.seats                          # {"A": 132, "B": 132, ...}
    r.ejected                        # parties that missed recognition
    r.can_act(["A", "C", "D"])       # meets the structural threshold?
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from math import ceil
from pathlib import Path

import yaml

DIVISORS = {
    "sainte_lague": lambda i: 2 * i + 1,
    "dhondt": lambda i: i + 1,
}


@dataclass(frozen=True)
class Fire:
    """A recognized slot. Usually one party; more if they share a lineage."""

    name: str
    parties: tuple[str, ...]
    votes: float
    seats: int


@dataclass(frozen=True)
class Allocation:
    seats: dict[str, int]
    fires: tuple[Fire, ...]
    ejected: tuple[str, ...]
    chamber: int
    fires_required: int
    seat_majority: bool

    def share(self, party: str) -> float:
        return 100 * self.seats.get(party, 0) / self.chamber

    def fire_of(self, party: str) -> Fire | None:
        return next((f for f in self.fires if party in f.parties), None)

    def can_act(self, parties) -> bool:
        """Does this coalition meet the structural threshold?"""
        held = {f.name for p in parties if (f := self.fire_of(p))}
        if len(held) < self.fires_required:
            return False
        return not self.seat_majority or self._majority(parties)

    def can_pass(self, parties) -> bool:
        """Ordinary legislation: a seat majority, nothing more."""
        return self._majority(parties)

    def coalitions(self, test=None) -> list[tuple[str, ...]]:
        """Minimal party-sets satisfying `test` (default: can_pass)."""
        test = test or self.can_pass
        found = [
            c
            for n in range(1, len(self.seats) + 1)
            for c in combinations(self.seats, n)
            if test(c)
        ]
        return sorted(
            (c for c in found if not any(set(o) < set(c) for o in found)),
            key=lambda c: sum(self.seats[p] for p in c),
        )

    def _majority(self, parties) -> bool:
        return sum(self.seats.get(p, 0) for p in parties) * 2 > self.chamber

    def __str__(self) -> str:
        width = max((len(n) for n in self.seats), default=5)
        rows = sorted(self.seats.items(), key=lambda kv: -kv[1])
        body = "\n".join(
            f"{n:<{width}}{s:>7}{self.share(n):>8.1f}%" for n, s in rows
        )
        tail = f"\nejected: {', '.join(self.ejected)}" if self.ejected else ""
        return f"{'party':<{width}}{'seats':>7}{'share':>9}\n{body}{tail}"


@dataclass
class Distributor:
    """Seat distributor for the Five Fires system.
    
    Core assumptions:
    - Each party occupies exactly one fire (no lineage grouping)
    - Under Sainte-Lague divisor, splitting a party into two equal parts
      gains more total seats than staying as one party
    - This natural incentive encourages parties to split, maintaining
      the five-party balance without explicit bonus seats
    """
    fires: int = 5
    seats: int = 400
    divisor: str = "sainte_lague"
    structural_fires: float = 0.6
    seat_majority: bool = True

    def __post_init__(self):
        if self.divisor not in DIVISORS:
            raise ValueError(f"unknown divisor {self.divisor!r}")
        if not 0 < self.structural_fires <= 1:
            raise ValueError("structural fires must be a fraction in (0, 1]")
        # Verify splitting incentive for Sainte-Lague (core assumption)
        if self.divisor == "sainte_lague":
            self._verify_splitting_incentive()

    def _verify_splitting_incentive(self):
        """Assert that splitting a large party into two equal parts gains seats.
        
        This is the core mechanical incentive that maintains the five-party balance.
        Under Sainte-Lague with independent fires, splitting is always beneficial.
        """
        # Test case: 40% party vs two 20% parties
        base = self({"A": 40, "B": 20, "C": 20, "D": 15, "E": 5})
        split = self({"A1": 20, "A2": 20, "B": 20, "C": 15, "D": 10, "E": 5})
        
        a_seats = base.seats["A"]
        a1_a2_seats = split.seats["A1"] + split.seats["A2"]
        
        assert a1_a2_seats > a_seats, (
            f"Splitting incentive broken: {a1_a2_seats} <= {a_seats}. "
            f"Splitting should gain seats under Sainte-Lague with independent fires."
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> Distributor:
        cfg = yaml.safe_load(Path(path).read_text())
        return cls(
            fires=cfg["fires"],
            seats=cfg["seats"],
            divisor=cfg["allocation"]["divisor"],
            structural_fires=cfg["structural"]["fires"],
            seat_majority=cfg["structural"]["seat_majority"],
        )

    def distribute(self, votes: dict[str, float]) -> Allocation:
        groups = self._group(votes)
        winners, losers = groups[: self.fires], groups[self.fires :]
        recognized = [p for g in winners for p in g]

        seats = self._apportion({p: votes[p] for p in recognized})

        return Allocation(
            seats=seats,
            fires=tuple(
                Fire(
                    name="+".join(sorted(g)),
                    parties=tuple(g),
                    votes=sum(votes[p] for p in g),
                    seats=sum(seats[p] for p in g),
                )
                for g in winners
            ),
            ejected=tuple(p for g in losers for p in g),
            chamber=self.seats,
            fires_required=ceil(self.structural_fires * len(winners)),
            seat_majority=self.seat_majority,
        )

    __call__ = distribute

    def _group(self, votes) -> list[list[str]]:
        """Parties into fire-groups, ranked by vote."""
        return sorted([[p] for p in votes], key=lambda g: -sum(votes[p] for p in g))

    def _apportion(self, pool: dict[str, float]) -> dict[str, int]:
        """Highest-quotient allocation under the configured divisor."""
        d = DIVISORS[self.divisor]
        out = dict.fromkeys(pool, 0)
        for _ in range(self.seats):
            out[max(pool, key=lambda p: pool[p] / d(out[p]))] += 1
        return out
