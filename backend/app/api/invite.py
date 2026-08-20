"""Anonymous responder endpoints (docs/03-lld.md §3.4–3.5).

Authorized purely by the unguessable link token in the path, no account. The
response POST returns no stored data, so it can never leak another person's
answers (invariant I1).
"""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import get_settings
from app.core.ratelimit import response_limiter
from app.db import repo
from app.models.schemas import InviteSummary, ResponseAck, ResponseCreate, SlotOut

router = APIRouter(prefix="/api/invite", tags=["invite"])


def _first_name(catchup: dict) -> str | None:
    profile = catchup.get("profiles")
    name = profile.get("display_name") if isinstance(profile, dict) else None
    return name.split()[0] if name else None


def _sorted_slots(catchup: dict) -> list[dict]:
    return sorted(catchup.get("slots") or [], key=lambda s: s.get("sort_order", 0))


@router.get("/{link_token}", response_model=InviteSummary)
def get_invite(link_token: str) -> InviteSummary:
    catchup = repo.get_catchup_by_link_token(link_token)
    if catchup is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invite not found")

    return InviteSummary(
        title=catchup["title"],
        message=catchup.get("message"),
        location=catchup.get("location"),
        type=catchup["type"],
        creator_first_name=_first_name(catchup),
        deadline=catchup.get("deadline"),
        status=catchup["status"],
        slots=[SlotOut(**s) for s in _sorted_slots(catchup)],
    )


@router.post(
    "/{link_token}/responses",
    response_model=ResponseAck,
    status_code=status.HTTP_201_CREATED,
)
def submit_response(link_token: str, payload: ResponseCreate, request: Request) -> ResponseAck:
    # Honeypot: real users never fill the hidden `website` field. Silently
    # accept (200-ish) so bots get no signal, but store nothing.
    if payload.website:
        return ResponseAck()

    ip = request.client.host if request.client else "unknown"
    if not response_limiter.allow(f"{ip}:{link_token}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too many submissions, please slow down",
        )

    catchup = repo.get_catchup_by_link_token(link_token)
    if catchup is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invite not found")

    # Response cap: min(creator's limit, server hard cap). Bounds DB pollution.
    hard_cap = get_settings().response_hard_cap
    creator_max = catchup.get("max_responses")
    effective_cap = min(creator_max, hard_cap) if creator_max else hard_cap
    if repo.response_count(catchup) >= effective_cap:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="this catch-up has reached its response limit",
        )

    if catchup["status"] != "open":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="this catch-up is closed")

    deadline = catchup.get("deadline")
    if deadline:
        due = datetime.fromisoformat(deadline)
        if due.tzinfo is None:
            due = due.replace(tzinfo=UTC)
        if datetime.now(UTC) > due:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="the response deadline has passed"
            )

    valid_slot_ids = {s["id"] for s in (catchup.get("slots") or [])}
    unknown = [sid for sid in payload.slot_ids if sid not in valid_slot_ids]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="one or more selected time options are not part of this catch-up",
        )

    repo.create_response(catchup["id"], payload.model_dump(), payload.slot_ids)
    return ResponseAck()
