"""
Five Fires — seat distributor.

    from distributor import Distributor

    d = Distributor.from_yaml("config.yaml")
    r = d({"A": 33, "B": 33, "C": 11, "D": 11, "E": 11})

    r.seats                          # {"A": 120, "B": 120, ...}
    r.cold                           # seats the cap left vacant
    r.council                        # one voice per fire
    r.ejected                        # parties that missed recognition
    r.can_act(["A", "C", "D"])       # both keys turned?

Two moves are available to a party, and both happen before the ballot:
divide, or merge. The rules price them.

    cap     a fire may hold no more than `cap` of the chamber. Seats above
            that are left cold — vacant, not handed to rivals. Staying whole
            past the cap forfeits them. Dividing claims them.

    cliff   only the top `fires` parties are recognized; everyone else's
            votes are wasted. Divide too far and each shard sits close to
            the cliff edge, where a bad night costs a whole fire.

Together they bracket a fire at roughly a fifth to a third of the chamber:
merge upward off the cliff, divide downward off the cap.

Nothing here reads party identity or lineage. A party that divides in name
only is free to merge back, and the cap will take the seats off it when it
does. There is no test of sincerity because there is no referee to apply one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from math import ceil, floor
from pathlib import Path

import yaml

DIVISORS = {
    "sainte_lague": lambda i: 2 * i + 1,
    "dhondt": lambda i: i + 1,
}


@dataclass(frozen=True)
class Fire:
    """A recognized slot, and one seat on the council.

    `parties` holds one name, except where parties ejected on the count
    merged afterwards to claim the fire between them (see `rescue`).
    """

    name: str
    parties: tuple[str, ...]
    votes: float
    seats: int
    cold: int = 0

    @property
    def claimed(self) -> int:
        """Seats this fire won before the cap took the excess."""
        return self.seats + self.cold


@dataclass(frozen=True)
class Allocation:
    seats: dict[str, int]
    fires: tuple[Fire, ...]
    ejected: tuple[str, ...]
    chamber: int
    fires_required: int
    seat_supermajority: float
    rescued: tuple[tuple[str, ...], ...] = ()

    @property
    def cold(self) -> int:
        """Seats left vacant because a fire outgrew the cap."""
        return sum(f.cold for f in self.fires)

    @property
    def council(self) -> tuple[str, ...]:
        """One voice per fire, regardless of size."""
        return tuple(f.name for f in self.fires)

    @property
    def wasted(self) -> float:
        """Share of the vote cast for parties that hold no fire."""
        held = sum(f.votes for f in self.fires)
        return 0.0 if not held else 100 * (1 - held / (held + self._lost))

    def share(self, party: str) -> float:
        return 100 * self.seats.get(party, 0) / self.chamber

    def fire_of(self, party: str) -> Fire | None:
        return next((f for f in self.fires if party in f.parties), None)

    def council_votes(self, parties) -> int:
        """How many fires a set of parties speaks for."""
        return len({f.name for p in parties if (f := self.fire_of(p))})

    def can_act(self, parties) -> bool:
        """Structural action — both keys turned: the council and the chamber.

        The seat key is a supermajority, not a majority, and that is
        deliberate. A single bloc that divides itself three ways can hold
        three of five fires and a bare majority of seats; two thirds is out
        of its reach.
        """
        return (
            self.council_votes(parties) >= self.fires_required
            and self.has_supermajority(parties)
        )

    def can_pass(self, parties) -> bool:
        """Ordinary legislation: a seat majority, nothing more."""
        return self._held(parties) * 2 > self.chamber

    def has_supermajority(self, parties) -> bool:
        return self._held(parties) >= ceil(self.seat_supermajority * self.chamber)

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

    def _held(self, parties) -> int:
        return sum(self.seats.get(p, 0) for p in parties)

    _lost: float = field(default=0.0, repr=False)

    def __str__(self) -> str:
        width = max((len(n) for n in self.seats), default=5)
        rows = sorted(self.seats.items(), key=lambda kv: -kv[1])
        body = "\n".join(
            f"{n:<{width}}{s:>7}{self.share(n):>8.1f}%" for n, s in rows
        )
        tail = ""
        if self.cold:
            tail += f"\ncold: {self.cold} seats vacant (cap)"
        if self.rescued:
            tail += "\nrescued: " + ", ".join("+".join(g) for g in self.rescued)
        if self.ejected:
            tail += f"\nejected: {', '.join(self.ejected)}"
        return f"{'party':<{width}}{'seats':>7}{'share':>9}\n{body}{tail}"


@dataclass
class Distributor:
    """Seat distributor for the Five Fires system.

    Recognition goes to the top `fires` parties by vote. Votes cast for
    anyone else are wasted and redistribute among those recognized.

    A fire may hold at most `cap` of the chamber; seats above that are left
    cold rather than passed to rivals, so refusing to divide costs the
    hoarder alone and elevates nobody artificially.

    Sainte-Lague is here for proportionality, not for any splitting bonus —
    a divisor cannot supply one. Under either divisor a party that divides
    holds exactly the seats it held before; the incentive to divide comes
    from the cap, and the incentive not to over-divide from the cliff.
    """

    fires: int = 5
    seats: int = 400
    divisor: str = "sainte_lague"
    cap: float | None = 0.30
    rescue: bool = False
    rescue_floor: float = 0.0
    structural_fires: float = 0.6
    seat_supermajority: float = 0.667

    def __post_init__(self):
        if self.divisor not in DIVISORS:
            raise ValueError(f"unknown divisor {self.divisor!r}")
        if not 0 < self.structural_fires <= 1:
            raise ValueError("structural fires must be a fraction in (0, 1]")
        if not 0.5 < self.seat_supermajority <= 1:
            raise ValueError("seat supermajority must be a fraction in (0.5, 1]")
        if self.cap is not None and not 1 / self.fires <= self.cap <= 1:
            raise ValueError(
                f"cap must fall between an equal share (1/{self.fires}) and 1"
            )
        if not 0 <= self.rescue_floor < 1 / self.fires:
            raise ValueError(
                f"rescue floor must sit below an equal share (1/{self.fires})"
            )

    @classmethod
    def from_yaml(cls, path: str | Path) -> Distributor:
        cfg = yaml.safe_load(Path(path).read_text())
        return cls(
            fires=cfg["fires"],
            seats=cfg["seats"],
            divisor=cfg["allocation"]["divisor"],
            cap=cfg["allocation"].get("cap"),
            rescue=cfg.get("rules", {}).get("rescue", False),
            rescue_floor=cfg.get("rules", {}).get("rescue_floor", 0.0),
            structural_fires=cfg["structural"]["fires"],
            seat_supermajority=cfg["structural"]["seat_supermajority"],
        )

    def distribute(self, votes: dict[str, float], rescue=None) -> Allocation:
        """Allocate the chamber.

        `rescue` — groups of parties, each of which must have been ejected on
        the count as cast, that have agreed to merge and claim a fire
        between them. Requires `rules.rescue`. A rescue can only ever be
        made by parties the ballot left out, so it lowers the wasted vote;
        it may still displace a smaller party that had been recognized.
        """
        groups = [(p,) for p in votes]
        rescued: tuple[tuple[str, ...], ...] = ()

        if rescue:
            if not self.rescue:
                raise ValueError("post-count rescue is off (rules.rescue)")
            rescued = self._validate_rescue(votes, rescue)
            merged = {p for g in rescued for p in g}
            groups = [(p,) for p in votes if p not in merged] + list(rescued)

        pool = {self._name(g): sum(votes[p] for p in g) for g in groups}
        winners = sorted(pool, key=lambda n: -pool[n])[: self.fires]

        seats, cold = self._apportion({n: pool[n] for n in winners})
        by_name = {self._name(g): g for g in groups}

        return Allocation(
            seats=seats,
            fires=tuple(
                Fire(
                    name=n,
                    parties=by_name[n],
                    votes=pool[n],
                    seats=seats[n],
                    cold=cold.get(n, 0),
                )
                for n in winners
            ),
            ejected=tuple(
                p for g in groups for p in g if self._name(g) not in winners
            ),
            chamber=self.seats,
            fires_required=ceil(self.structural_fires * len(winners)),
            seat_supermajority=self.seat_supermajority,
            rescued=rescued,
            _lost=sum(pool[n] for n in pool if n not in winners),
        )

    __call__ = distribute

    def viable_rescues(self, votes: dict[str, float], limit: int = 4):
        """Minimal groups of ejected parties that would claim a fire together."""
        base = self.distribute(votes)
        out = list(self.eligible(votes))
        smallest = min((f.votes for f in base.fires), default=0.0)
        found = [
            g
            for n in range(2, min(limit, len(out)) + 1)
            for g in combinations(out, n)
            if sum(votes[p] for p in g) > smallest
        ]
        return sorted(
            (g for g in found if not any(set(o) < set(g) for o in found)),
            key=lambda g: -sum(votes[p] for p in g),
        )

    @staticmethod
    def _name(group: tuple[str, ...]) -> str:
        return group[0] if len(group) == 1 else "+".join(sorted(group))

    def eligible(self, votes: dict[str, float]) -> tuple[str, ...]:
        """Ejected parties whose own vote clears the rescue floor.

        The floor is what separates a rescue from a vacuum cleaner. Without
        it any pile of micro-parties can assemble a fire between them; with
        it, a rescue is only available to parties that carried real support
        and lost to the cliff. The cost is that everything below the floor
        stays wasted.
        """
        total = sum(votes.values())
        return tuple(
            p
            for p in self.distribute(votes).ejected
            if total and votes[p] / total >= self.rescue_floor
        )

    def _validate_rescue(self, votes, rescue) -> tuple[tuple[str, ...], ...]:
        """A rescue group is parties the ballot ejected, who may either merge
        with each other or join one fire that is already tended.

        At most one member may hold a fire. Two would be a post-count merger
        of two fires, which frees a slot and lets the sixth party in -- the
        ballot deciding one thing and the chamber another.
        """
        base = self.distribute(votes)
        allowed = set(self.eligible(votes))
        ejected = set(base.ejected)
        total = sum(votes.values())
        limit = None if self.cap is None else floor(self.cap * self.seats)
        seen: set[str] = set()
        out = []
        for group in rescue:
            g = tuple(group)
            if len(g) < 2:
                raise ValueError(f"a rescue needs two or more parties: {g}")
            hosts = [p for p in g if p in votes and p not in ejected]
            if len(hosts) > 1:
                raise ValueError(
                    f"{', '.join(hosts)} all tend fires; a rescue may join "
                    "at most one"
                )
            if hosts and limit is not None and base.seats[hosts[0]] >= limit:
                # A fire at the cap gains no seats by taking on more, so it
                # can outbid every other host at no cost to itself -- and
                # burn the votes it takes. A full fire takes no more fuel.
                raise ValueError(
                    f"{hosts[0]!r} is at the cap and has no room to host"
                )
            for p in g:
                if p not in votes:
                    raise ValueError(f"unknown party {p!r}")
                if p in seen:
                    raise ValueError(f"{p!r} appears in two rescues")
                seen.add(p)
                if p in hosts:
                    continue
                if p not in allowed:
                    raise ValueError(
                        f"{p!r} holds {100 * votes[p] / total:.1f}%, below the "
                        f"{100 * self.rescue_floor:.1f}% rescue floor"
                    )
            out.append(g)
        return tuple(out)

    def _apportion(self, pool: dict[str, float]):
        """Highest-quotient allocation, then the cap takes the excess cold."""
        d = DIVISORS[self.divisor]
        out = dict.fromkeys(pool, 0)
        for _ in range(self.seats):
            out[max(pool, key=lambda p: pool[p] / d(out[p]))] += 1

        if self.cap is None:
            return out, {}

        limit = floor(self.cap * self.seats)
        cold = {p: out[p] - limit for p in out if out[p] > limit}
        for p in cold:
            out[p] = limit
        return out, cold


def divide(votes: dict[str, float], party: str, parts: dict[str, float]):
    """Split `party` into `parts` (name -> share of its vote). Pre-ballot."""
    if abs(sum(parts.values()) - 1) > 1e-9:
        raise ValueError("parts must sum to 1")
    out = {p: v for p, v in votes.items() if p != party}
    for name, frac in parts.items():
        out[name] = votes[party] * frac
    return out


def merge(votes: dict[str, float], parties, name: str | None = None):
    """Merge `parties` onto one ballot line. Pre-ballot."""
    parties = tuple(parties)
    out = {p: v for p, v in votes.items() if p not in parties}
    out[name or "+".join(sorted(parties))] = sum(votes[p] for p in parties)
    return out
