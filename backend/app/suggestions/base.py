"""Suggestion provider interface (docs/03-lld.md §6).

Callers depend on this interface, not the concrete provider, so an AI-backed
implementation can replace the rules engine later with no changes upstream.
"""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class SuggestionContext:
    type: str  # catch-up type: casual|food|activity|outing|trip
    band_low: int  # recommended per-person low
    band_high: int  # recommended per-person high
    interests: list[str] = field(default_factory=list)  # aggregated across attendees
    group_size: int = 0


@dataclass
class Suggestion:
    title: str
    blurb: str
    est_per_person_low: int
    est_per_person_high: int
    tags: list[str] = field(default_factory=list)


class SuggestionProvider(Protocol):
    def suggest(self, ctx: SuggestionContext) -> list[Suggestion]: ...
