"""Creator endpoints for catch-ups (docs/03-lld.md §3.1–3.3)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import User, get_current_user
from app.core.config import get_settings
from app.db import repo
from app.models.schemas import (
    CatchupCreate,
    CatchupCreated,
    CatchupDetail,
    CatchupListItem,
    SlotOut,
    StatusOut,
)

router = APIRouter(prefix="/api/catchups", tags=["catchups"])


@router.post("", response_model=CatchupCreated, status_code=status.HTTP_201_CREATED)
def create_catchup(
    payload: CatchupCreate, user: User = Depends(get_current_user)
) -> CatchupCreated:
    # Make sure the owner has a profile row (FK target) before inserting.
    repo.upsert_profile(user.id, user.email, user.display_name)

    data = payload.model_dump(mode="json", exclude={"slots"})
    slots = [s.model_dump(mode="json") for s in payload.slots]
    catchup = repo.create_catchup(user.id, data, slots)

    base = get_settings().frontend_base_url.rstrip("/")
    return CatchupCreated(
        id=catchup["id"],
        link_token=catchup["link_token"],
        result_token=catchup["result_token"],
        invite_url=f"{base}/r/{catchup['link_token']}",
        result_url=f"{base}/result/{catchup['result_token']}",
    )


@router.get("", response_model=list[CatchupListItem])
def list_catchups(user: User = Depends(get_current_user)) -> list[CatchupListItem]:
    rows = repo.list_catchups(user.id)
    return [
        CatchupListItem(
            id=r["id"],
            title=r["title"],
            type=r["type"],
            status=r["status"],
            response_count=repo.response_count(r),
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.get("/{catchup_id}", response_model=CatchupDetail)
def get_catchup(catchup_id: str, user: User = Depends(get_current_user)) -> CatchupDetail:
    catchup = repo.get_catchup(catchup_id)
    # 404 (not 403) when missing OR not owned, never reveal another user's data.
    if catchup is None or catchup["owner_id"] != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="catch-up not found")

    slots = sorted(catchup.get("slots") or [], key=lambda s: s.get("sort_order", 0))
    return CatchupDetail(
        id=catchup["id"],
        title=catchup["title"],
        message=catchup.get("message"),
        location=catchup.get("location"),
        type=catchup["type"],
        status=catchup["status"],
        deadline=catchup.get("deadline"),
        slots=[SlotOut(**s) for s in slots],
        response_count=repo.response_count(catchup),
    )


@router.post("/{catchup_id}/close", response_model=StatusOut)
def close_catchup(catchup_id: str, user: User = Depends(get_current_user)) -> StatusOut:
    catchup = repo.get_catchup(catchup_id)
    if catchup is None or catchup["owner_id"] != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="catch-up not found")
    repo.set_catchup_status(catchup_id, "closed")
    return StatusOut(status="closed")
