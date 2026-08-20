"""Results endpoints, aggregate-only (docs/03-lld.md §3.6).

Ties matching + budget + suggestions together. Returns only aggregates and
first names; there is no path here that exposes an individual's budget or
availability (invariant I1)."""

from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.budget.engine import compute_band, expand_people
from app.core.auth import User, get_current_user
from app.db import repo
from app.matching.engine import Response, Slot, attendees_of, match
from app.models.schemas import (
    AlternativeOut,
    BestSlotOut,
    BudgetOut,
    MoneyBand,
    ResultOut,
    SuggestionOut,
)
from app.suggestions.base import SuggestionContext
from app.suggestions.rules import RulesSuggestionProvider

router = APIRouter(tags=["results"])

_suggester = RulesSuggestionProvider()


def _parse_dt(value: str) -> datetime:
    # PostgREST returns ISO 8601; normalise trailing Z for fromisoformat.
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _first_name(full: str) -> str:
    return full.split()[0] if full else full


def _slot_label(slot: Slot) -> str:
    if slot.label:
        return slot.label
    return slot.starts_at.strftime("%a %d %b, %I:%M %p").replace(" 0", " ")


def build_result(catchup: dict) -> ResultOut:
    slots = [
        Slot(
            id=s["id"],
            starts_at=_parse_dt(s["starts_at"]),
            ends_at=_parse_dt(s["ends_at"]),
            label=s.get("label"),
            sort_order=s.get("sort_order", 0),
        )
        for s in (catchup.get("slots") or [])
    ]
    raw_responses = catchup.get("responses") or []
    responses = [
        Response(
            id=r["id"],
            slot_ids=[rs["slot_id"] for rs in (r.get("response_slots") or [])],
            companions=r.get("companions", 0),
            budget_min=r.get("budget_min", 0),
            budget_max=r.get("budget_max", 0),
            contribution=r.get("contribution", 0),
            interests=r.get("interests") or [],
        )
        for r in raw_responses
    ]
    responded = [_first_name(r.get("name", "")) for r in raw_responses]
    response_count = len(responses)

    if response_count == 0:
        return ResultOut(
            response_count=0,
            responded=[],
            message="Waiting for responses. Share the invite link to get started.",
        )

    result = match(responses, slots)

    if result.best is None:
        alts = [
            AlternativeOut(
                id=s.slot.id,
                starts_at=s.slot.starts_at,
                ends_at=s.slot.ends_at,
                label=s.slot.label,
                attending_headcount=s.headcount,
            )
            for s in result.alternatives
        ]
        return ResultOut(
            best_slot=None,
            alternatives=alts,
            response_count=response_count,
            responded=responded,
            message="No single time works for the group yet. Here are the closest options.",
        )

    best = result.best
    attendees = attendees_of(best.slot.id, responses)
    group_size = best.headcount

    band = compute_band(expand_people(attendees), group_size)
    contributions_total = sum(r.contribution for r in attendees)

    interest_counts = Counter()
    for r in attendees:
        interest_counts.update(r.interests)
    top_interests = [name for name, _ in interest_counts.most_common()]

    suggestions = _suggester.suggest(
        SuggestionContext(
            type=catchup["type"],
            band_low=band.per_person_low,
            band_high=band.per_person_high,
            interests=top_interests,
            group_size=group_size,
        )
    )

    rationale = (
        f"Most people are free {_slot_label(best.slot)}, and "
        f"₹{band.per_person_low}–{band.per_person_high} per person works comfortably "
        f"for almost everyone."
    )

    return ResultOut(
        best_slot=BestSlotOut(
            id=best.slot.id,
            starts_at=best.slot.starts_at,
            ends_at=best.slot.ends_at,
            label=best.slot.label,
            attending_headcount=best.headcount,
            attending_people=best.people,
        ),
        alternatives=[
            AlternativeOut(
                id=s.slot.id,
                starts_at=s.slot.starts_at,
                ends_at=s.slot.ends_at,
                label=s.slot.label,
                attending_headcount=s.headcount,
            )
            for s in result.alternatives
        ],
        group_size=group_size,
        budget=BudgetOut(
            per_person=MoneyBand(low=band.per_person_low, high=band.per_person_high),
            total=MoneyBand(low=band.total_low, high=band.total_high),
            currency=band.currency,
            inclusion_pct=band.inclusion_pct,
            contributions_total=contributions_total,
            method=band.method,
        ),
        suggestions=[
            SuggestionOut(
                title=s.title,
                blurb=s.blurb,
                est_per_person=MoneyBand(low=s.est_per_person_low, high=s.est_per_person_high),
                tags=s.tags,
            )
            for s in suggestions
        ],
        rationale=rationale,
        responded=responded,
        response_count=response_count,
    )


@router.get("/api/catchups/{catchup_id}/results", response_model=ResultOut)
def owner_results(catchup_id: str, user: User = Depends(get_current_user)) -> ResultOut:
    catchup = repo.get_catchup_for_results(catchup_id=catchup_id)
    if catchup is None or catchup["owner_id"] != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="catch-up not found")
    return build_result(catchup)


@router.get("/api/results/{result_token}", response_model=ResultOut)
def shared_results(result_token: str) -> ResultOut:
    catchup = repo.get_catchup_for_results(result_token=result_token)
    if catchup is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="results not found")
    return build_result(catchup)
