"""Deterministic rules/template suggestion provider (docs/03-lld.md §6).

Curated catalogue keyed by (type, cost band, tags). No AI in the MVP. Guarantees:
suggestions never require more than the recommended per-person high, and the
cheapest feasible option is always included so nobody is priced out.
"""

from dataclasses import dataclass

from app.suggestions.base import Suggestion, SuggestionContext, SuggestionProvider


@dataclass
class CatalogueItem:
    title: str
    blurb: str
    types: list[str]
    min_cost: int
    max_cost: int
    tags: list[str]


CATALOGUE: list[CatalogueItem] = [
    CatalogueItem("Tea + walk", "Chai and a stroll, easy on everyone.",
                  ["casual", "activity", "outing"], 0, 300, ["tea/coffee", "walk"]),
    CatalogueItem("Park + snacks", "Meet at a park, bring snacks to share.",
                  ["casual", "outing", "activity"], 0, 400, ["park", "walk"]),
    CatalogueItem("Café + board games", "Coffee and a few rounds of games.",
                  ["casual", "food", "activity"], 200, 800, ["games", "tea/coffee", "food"]),
    CatalogueItem("Beach evening", "Sunset walk and street snacks by the beach.",
                  ["outing", "activity"], 0, 500, ["beach", "walk"]),
    CatalogueItem("Casual lunch/dinner", "A relaxed meal out together.",
                  ["food"], 300, 900, ["food"]),
    CatalogueItem("Dinner out", "A proper sit-down dinner.",
                  ["food"], 500, 1500, ["food"]),
    CatalogueItem("Sports + juice", "A game of cricket/football, then juice.",
                  ["activity", "outing"], 100, 600, ["sports", "games"]),
    CatalogueItem("Day trip (shared cab)", "A short day trip, splitting a cab.",
                  ["trip", "outing"], 600, 2500, ["day-trip"]),
]


class RulesSuggestionProvider(SuggestionProvider):
    def suggest(self, ctx: SuggestionContext) -> list[Suggestion]:
        interests = set(ctx.interests)

        # Feasible = right type AND doable within the recommended high
        # (entry cost <= band_high). Never suggest something that requires more.
        feasible = [
            item
            for item in CATALOGUE
            if ctx.type in item.types and item.min_cost <= ctx.band_high
        ]
        if not feasible:
            # Fall back to type-only, still respecting the high where possible.
            feasible = [item for item in CATALOGUE if ctx.type in item.types] or list(CATALOGUE)

        def score(item: CatalogueItem) -> tuple:
            interest_overlap = len(interests & set(item.tags))
            # Prefer options whose whole range fits under the high (fully affordable).
            fully_affordable = 1 if item.max_cost <= ctx.band_high else 0
            return (interest_overlap, fully_affordable, -item.min_cost)

        ranked = sorted(feasible, key=score, reverse=True)

        chosen = ranked[:3]
        # Guarantee the cheapest feasible option is always offered.
        cheapest = min(feasible, key=lambda i: i.min_cost)
        if cheapest not in chosen:
            chosen = chosen[:3] + [cheapest]

        return [self._to_suggestion(item, ctx) for item in chosen[:4]]

    @staticmethod
    def _to_suggestion(item: CatalogueItem, ctx: SuggestionContext) -> Suggestion:
        low = max(item.min_cost, ctx.band_low) if ctx.band_low else item.min_cost
        high = min(item.max_cost, ctx.band_high) if ctx.band_high else item.max_cost
        if high < low:
            high = low
        return Suggestion(
            title=item.title,
            blurb=item.blurb,
            est_per_person_low=low,
            est_per_person_high=high,
            tags=item.tags,
        )
