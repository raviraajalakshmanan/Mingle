"""Comfortable-group-budget computation (docs/03-lld.md §5).

The product's differentiator: recommend a spending band the *group* is
comfortable with, explicitly resistant to a single high outlier. We anchor on a
percentile of per-person comfort maxima (never the sum or mean), then apply an
inclusion floor so inclusiveness dominates.
"""

from dataclasses import dataclass

# --- tunable config (docs/03-lld.md §5.4) -----------------------------------
P_HIGH = 60  # percentile of per-person max used for the top of the band
P_LOW = 30  # percentile of per-person min used for the bottom of the band
INCLUSION_FLOOR = 0.70  # keep >= this fraction of people comfortable
ROUND_TO = 50  # round band edges to nearest this many rupees
CURRENCY = "INR"


@dataclass
class BudgetInput:
    """One person's comfort band. Companions are expanded into separate entries
    upstream (each inherits the responder's band), so every entry == one person."""

    budget_min: int
    budget_max: int


@dataclass
class BudgetBand:
    per_person_low: int
    per_person_high: int
    total_low: int
    total_high: int
    inclusion_pct: float
    currency: str = CURRENCY
    method: str = "comfortable-group-budget"


def percentile(sorted_values: list[int], pct: float) -> float:
    """Linear-interpolation percentile (like numpy's default)."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = (pct / 100.0) * (len(sorted_values) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = rank - lo
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac


def _round_to(value: float, step: int) -> int:
    return int(round(value / step) * step)


def _inclusion(person_maxes: list[int], high: int) -> float:
    if not person_maxes:
        return 0.0
    comfortable = sum(1 for m in person_maxes if m >= high)
    return comfortable / len(person_maxes)


def compute_band(people: list[BudgetInput], group_size: int) -> BudgetBand:
    """Compute the recommended band for the given per-person comfort inputs.

    `group_size` is the total headcount at the chosen slot (used for totals);
    it should equal len(people) once companions are expanded.
    """
    if not people:
        return BudgetBand(0, 0, 0, 0, 0.0)

    maxes = sorted(p.budget_max for p in people)
    mins = sorted(p.budget_min for p in people)

    high = _round_to(percentile(maxes, P_HIGH), ROUND_TO)
    low = _round_to(percentile(mins, P_LOW), ROUND_TO)

    # Inclusion floor: if too few people are comfortable at `high`, lower it to
    # the largest actual comfort-max that keeps >= INCLUSION_FLOOR comfortable.
    if _inclusion(maxes, high) < INCLUSION_FLOOR:
        distinct_desc = sorted(set(maxes), reverse=True)
        for candidate in distinct_desc:
            if candidate <= high and _inclusion(maxes, candidate) >= INCLUSION_FLOOR:
                high = candidate
                break

    # Keep the band coherent.
    if low > high:
        low = min(mins)
    low = min(low, high)

    inclusion_pct = round(_inclusion(maxes, high) * 100, 1)

    return BudgetBand(
        per_person_low=low,
        per_person_high=high,
        total_low=low * group_size,
        total_high=high * group_size,
        inclusion_pct=inclusion_pct,
    )


def expand_people(responses) -> list[BudgetInput]:
    """Expand responses into one BudgetInput per person (companions inherit the
    responder's band, OQ-3). `responses` items must expose budget_min/max and
    companions (matching.engine.Response works directly)."""
    people: list[BudgetInput] = []
    for r in responses:
        for _ in range(1 + r.companions):
            people.append(BudgetInput(budget_min=r.budget_min, budget_max=r.budget_max))
    return people
