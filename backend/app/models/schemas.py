"""Pydantic request/response models for the API (docs/03-lld.md §3)."""

from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field, model_validator

CatchupType = Literal["casual", "food", "activity", "outing", "trip"]

# Clocks drift and requests take a moment to arrive, so a time this far behind
# the server clock still counts as "now" instead of being rejected as past.
PAST_GRACE = timedelta(minutes=2)


def _utc(value: datetime) -> datetime:
    """Read a naive datetime as UTC so comparisons never mix aware and naive."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _is_past(value: datetime) -> bool:
    return _utc(value) < datetime.now(UTC) - PAST_GRACE


# --- Create catch-up ---------------------------------------------------------


class SlotIn(BaseModel):
    starts_at: datetime
    ends_at: datetime
    label: str | None = None

    @model_validator(mode="after")
    def _check_times(self) -> "SlotIn":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        # A catch-up can only be planned forwards. See docs/03-lld.md.
        if _is_past(self.starts_at):
            raise ValueError("starts_at must not be in the past")
        return self


class CatchupCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    message: str | None = Field(default=None, max_length=2000)
    location: str | None = Field(default=None, max_length=200)
    type: CatchupType
    slots: list[SlotIn] = Field(min_length=1, max_length=20)
    deadline: datetime | None = None
    # Optional creator-set cap on responses. Clamped server-side to the hard cap.
    max_responses: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _deadline_not_past(self) -> "CatchupCreate":
        if self.deadline is not None and _is_past(self.deadline):
            raise ValueError("deadline must not be in the past")
        return self


class CatchupCreated(BaseModel):
    id: str
    link_token: str
    result_token: str
    invite_url: str
    result_url: str


# --- Read models -------------------------------------------------------------


class SlotOut(BaseModel):
    id: str
    starts_at: datetime
    ends_at: datetime
    label: str | None = None
    sort_order: int = 0


class CatchupListItem(BaseModel):
    id: str
    title: str
    type: CatchupType
    status: str
    response_count: int
    created_at: datetime


class CatchupDetail(BaseModel):
    id: str
    title: str
    message: str | None = None
    location: str | None = None
    type: CatchupType
    status: str
    deadline: datetime | None = None
    slots: list[SlotOut]
    response_count: int


# --- Responder (anonymous) ---------------------------------------------------


class InviteSummary(BaseModel):
    """Public, read-only view for an invitee. Carries NO owner id or tokens."""

    title: str
    message: str | None = None
    location: str | None = None
    type: CatchupType
    creator_first_name: str | None = None
    deadline: datetime | None = None
    status: str
    slots: list[SlotOut]


class ResponseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    slot_ids: list[str] = Field(min_length=1, max_length=20)
    companions: int = Field(default=0, ge=0, le=50)
    budget_min: int = Field(ge=0, le=10_000_000)
    budget_max: int = Field(ge=0, le=10_000_000)
    contribution: int = Field(default=0, ge=0, le=10_000_000)
    interests: list[str] = Field(default_factory=list, max_length=20)
    # Honeypot: a hidden field real users never see. Any non-empty value marks
    # the submitter as a bot. Not persisted.
    website: str | None = None

    @model_validator(mode="after")
    def _budget_order(self) -> "ResponseCreate":
        if self.budget_max < self.budget_min:
            raise ValueError("budget_max must be >= budget_min")
        return self


class ResponseAck(BaseModel):
    # Intentionally carries no stored data, the submit endpoint must never
    # become a read side-channel (docs/03-lld.md §3.5, invariant I1).
    ok: bool = True


# --- Results (aggregate-only) ------------------------------------------------


class BestSlotOut(BaseModel):
    id: str
    starts_at: datetime
    ends_at: datetime
    label: str | None = None
    attending_headcount: int
    attending_people: int


class AlternativeOut(BaseModel):
    id: str
    starts_at: datetime
    ends_at: datetime
    label: str | None = None
    attending_headcount: int


class MoneyBand(BaseModel):
    low: int
    high: int


class BudgetOut(BaseModel):
    per_person: MoneyBand
    total: MoneyBand
    currency: str
    inclusion_pct: float
    contributions_total: int
    method: str


class SuggestionOut(BaseModel):
    title: str
    blurb: str
    est_per_person: MoneyBand
    tags: list[str]


class ResultOut(BaseModel):
    best_slot: BestSlotOut | None = None
    alternatives: list[AlternativeOut] = Field(default_factory=list)
    group_size: int = 0
    budget: BudgetOut | None = None
    suggestions: list[SuggestionOut] = Field(default_factory=list)
    rationale: str | None = None
    responded: list[str] = Field(default_factory=list)  # first names only (OQ-1)
    response_count: int = 0
    message: str | None = None


class StatusOut(BaseModel):
    status: str
