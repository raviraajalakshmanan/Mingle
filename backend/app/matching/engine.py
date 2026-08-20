"""Time-slot matching (docs/03-lld.md §4).

Pure functions over plain dataclasses, deterministic and unit-testable with no
DB. Best slot = the one with the greatest attending headcount (companions
counted), tie-broken by more people, then earlier start.
"""

from dataclasses import dataclass, field
from datetime import datetime

# A slot needs at least this many people to count as a real meetup.
MIN_MEANINGFUL_PEOPLE = 2


@dataclass
class Slot:
    id: str
    starts_at: datetime
    ends_at: datetime
    label: str | None = None
    sort_order: int = 0


@dataclass
class Response:
    id: str
    slot_ids: list[str]
    companions: int = 0
    budget_min: int = 0
    budget_max: int = 0
    contribution: int = 0
    interests: list[str] = field(default_factory=list)

    @property
    def headcount(self) -> int:
        return 1 + self.companions


@dataclass
class SlotScore:
    slot: Slot
    people: int
    headcount: int


def score_slots(responses: list[Response], slots: list[Slot]) -> list[SlotScore]:
    """Score every slot and return them ranked best-first."""
    scores: list[SlotScore] = []
    for slot in slots:
        attendees = [r for r in responses if slot.id in r.slot_ids]
        scores.append(
            SlotScore(
                slot=slot,
                people=len(attendees),
                headcount=sum(r.headcount for r in attendees),
            )
        )
    scores.sort(key=lambda s: (-s.headcount, -s.people, s.slot.starts_at))
    return scores


@dataclass
class MatchResult:
    best: SlotScore | None
    alternatives: list[SlotScore]
    no_overlap: bool


def match(responses: list[Response], slots: list[Slot]) -> MatchResult:
    ranked = score_slots(responses, slots)
    if not ranked or ranked[0].headcount == 0:
        # No responses at all.
        return MatchResult(best=None, alternatives=[], no_overlap=False)

    top = ranked[0]
    if top.people < MIN_MEANINGFUL_PEOPLE:
        # People responded but never on the same slot, surface the options.
        return MatchResult(best=None, alternatives=ranked[:3], no_overlap=True)

    alternatives = [s for s in ranked[1:] if s.headcount > 0][:3]
    return MatchResult(best=top, alternatives=alternatives, no_overlap=False)


def attendees_of(slot_id: str, responses: list[Response]) -> list[Response]:
    return [r for r in responses if slot_id in r.slot_ids]
