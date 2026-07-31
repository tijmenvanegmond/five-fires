# 🔥🔥🔥🔥🔥 The Five Fires System

**A managed five-party democracy for America.**

Seven rules. Five parties. One structural argument: governance distributed across five forces is more stable, more representative, and more resilient than a two-party binary.

And one property that holds across all seven: **no rule reads party identity or history — only vote counts.** There is nothing in the middle of this system for an authority to adjudicate, and therefore nothing worth capturing.

→ [Read the manifesto](manifesto.md)

---

## What is this?

A political architecture proposal that replaces America's two-party system with a constitutionally managed five-party democracy. Not a thought experiment — a working design with specific mechanics for elections, seat allocation, executive power, and direct democracy.

## The Seven Rules

1. **Five parties, always five.** Top five by vote share hold recognition. Sixth swaps in, lowest drops out. Votes below the line elect nobody — the cliff is deliberate.
2. **Proportional House, capped fires.** 400 seats. No fire holds more than 30% of the chamber; the excess is left cold, not given to rivals.
3. **Ranked-choice Senate.** Broad appeal required, not just base turnout.
4. **President with a sliding veto.** Two-round popular vote. Veto power weakens as Congressional majority grows.
5. **The Council of Five and the Firekeeper.** One voice per fire whatever its size, chaired by a nonpartisan Firekeeper elected by all of Congress. Councillors can't be recalled by their parties.
6. **Two keys for structural acts.** Three of five fires, plus two-thirds of the chamber. Ordinary law needs a majority and nothing more.
7. **Binding referendums.** Citizen-petitioned, majority wins, Congress can't override.

## Mechanics

A party has two moves, and both are made before the ballot: **divide** or **merge**. Two rules price them, and neither rule reads anything but vote counts.

**The cap.** A fire may hold at most 30% of the chamber. Seats above that are left *cold* — vacant, not handed to rivals. A 40% party that stays whole takes 120 seats and forfeits 73; divided into two 20% parties it takes 210 and forfeits none. Dividing is not a bonus, it is claiming seats you already won. Leaving the excess cold rather than redistributing it matters: hand those seats to rivals and the runner-up finishes ahead of the party that won the most votes, which would be indefensible.

**The cliff.** Only the top five parties are recognized; everyone else's votes are wasted. That punishes fragmentation at both ends. An 8% party that halves itself gets *zero* seats — both halves fall off the cliff. And a 40% party that divides four ways to farm council seats leaves each shard 2 points above the sixth-place party, where one bad night costs a whole fire.

Between them the two rules bracket a fire at roughly a fifth to a third of the chamber: merge upward off the cliff, divide downward off the cap.

**The council.** Each fire holds one seat on a council of five, chaired by the Firekeeper. The council turns the first of the two structural keys. This is what makes a division real rather than cosmetic: inside a 40% party a faction leader is a subordinate, but holding a fire makes them a constitutional officer, and re-merging costs one of the two their chair. The split is then defended by the person who gained from it. You cannot legislate sincerity, but you can create chairs.

**The structural key is two-thirds, not a majority.** A single bloc that divides itself three ways can hold three of five fires *and* a bare majority of seats — 235 of 400 in the worked case. Two-thirds is out of its reach: even dividing 52% of the national vote three ways reaches only 65% of the chamber, because the wasted vote it is exploiting is shared with its rivals.

**Post-count rescue (optional; enabled in the current config).** Parties the ballot left out may combine after the count — either merging with each other to claim a fire, or joining one fire already tended. The two are not equivalent:

| | wasted vote | who loses a fire |
|---|---|---|
| rescue off | 17% | — |
| the tail takes its own fire | 8% | the smallest seated party |
| the tail joins an existing fire | **1%** | **nobody** |

Merging is never additive: there are five fires, so a rescue that wins one necessarily unseats a party that won one on the night. Joining is additive and wastes less, but buys no council voice. That is the choice put to the tail — a voice of their own at someone else's expense, or seats inside another party's fire at nobody's.

Three limits keep it honest. A **participation floor** (2% of the vote) stops a rescue from being a vacuum cleaner that assembles a fire out of dust. **A fire at the cap may not host** — it gains no seats by taking more, so it could outbid every other host for free purely to deny them, and burn what it took. And **at most one seated party per rescue**, since two would be a post-count merger of fires that frees a slot and lets the sixth party in.

The standing objection, worth keeping in view while it is switched on: every other rule here settles the chamber at the ballot, and this one settles it in a room afterwards. Before the ballot voters can see a merger coming and judge it. After it, they cannot.

**Why lineage tracking is absent.** An earlier design merged parties sharing a lineage back into one fire, to stop cosmetic splits. That rule is gone. Enforcing it needs an authority ruling on which parties are "really" the same — a political question, not an administrative one, and the most capturable office in the system. It is unnecessary anyway: a party that divides in name only is free to merge back, and the cap takes the seats off it when it does.

**Note on the divisor.** Sainte-Laguë is here for proportionality, not for any splitting bonus. It does not supply one — under Sainte-Laguë *or* D'Hondt, a party that divides holds exactly the seats it held before. An earlier version of this section credited the divisor for an effect that actually came from the recognition rule. Every incentive to divide comes from the cap. Pinned by `test_divisor_supplies_no_splitting_bonus`.

## Historical precedent

Penta-governance has appeared independently across civilizations:

| System | Period | Region | Outcome |
|--------|--------|--------|---------|
| Haudenosaunee Confederacy | c. 1142–present | North America | Lasted centuries; directly influenced U.S. Constitution |
| Christian Pentarchy | c. 451–692 | Mediterranean | Held until external conquest removed three seats |
| Concert of Europe | 1815–1914 | Europe | Nearly a century of continental peace |
| Maratha Pentarchy | c. 1772–1818 | Indian subcontinent | Functioned but lacked structural binding; fell to internal rivalry and British divide-and-conquer |
| Chinese Wu Xing | Ancient–present | China | Philosophical framework for balanced cyclical governance |

The pattern: five-way governance is internally stable. It fails only when external forces overwhelm it or when the balance lacks structural enforcement.

## Related work

This proposal is a companion to [The Five Elements Republic](https://github.com/uDomkop/china/blob/main/five-elements-v2/five-elements-english.md) — a distributed governance model for Chinese unification rooted in Wu Xing philosophy. Same core conviction, opposite engineering problem:

- **Five Fires** (America): centrifugal — breaking a duopoly into dynamic competition
- **Five Elements** (China): centripetal — pulling separate entities into structured cooperation

## Key innovations

- **The cap and the cold seats** — a fire may hold at most 30% of the chamber, and the excess is left vacant rather than given to rivals, so refusing to divide costs the hoarder alone and elevates nobody artificially
- **The council of five** — one seat per fire regardless of size, which turns a division into two constitutional careers that cannot be recombined without someone losing a chair
- **Sliding veto** — presidential veto power scales inversely with Congressional majority size; strong against bare majorities, powerless against supermajorities
- **Managed party count** — constitutional cap at five recognized parties with automatic displacement, preventing both duopoly and fragmentation
- **The Firekeeper** — a structurally nonpartisan procedural role modeled on the Onondaga nation's function in the Haudenosaunee Confederacy

## Status

This is a proposal, not legislation. It is meant to be debated, stress-tested, and refined. If you see a flaw, open an issue. If you see a fix, open a PR.

## Author

DeDomkop · 2026

## License

This work is released into the public domain. Use it, adapt it, translate it, argue with it. Ideas that need permission aren't worth spreading.
