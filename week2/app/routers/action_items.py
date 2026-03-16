from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import db
from ..schemas import (
    ActionItemResponse,
    ExtractedItem,
    ExtractRequest,
    ExtractResponse,
    MarkDoneRequest,
    MarkDoneResponse,
)
from ..services.extract import extract_action_items

router = APIRouter(prefix="/action-items", tags=["action-items"])


@router.post("/extract", response_model=ExtractResponse)
def extract(payload: ExtractRequest) -> ExtractResponse:
    note_id: int | None = None
    if payload.save_note:
        note_id = db.insert_note(payload.text)

    try:
        items = extract_action_items(payload.text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Extraction failed: {exc}") from exc

    ids = db.insert_action_items(items, note_id=note_id)
    return ExtractResponse(
        note_id=note_id,
        items=[ExtractedItem(id=i, text=t) for i, t in zip(ids, items)],
    )


@router.get("", response_model=list[ActionItemResponse])
def list_all(note_id: int | None = None) -> list[ActionItemResponse]:
    return [ActionItemResponse(**row) for row in db.list_action_items(note_id=note_id)]


@router.post("/{action_item_id}/done", response_model=MarkDoneResponse)
def mark_done(action_item_id: int, payload: MarkDoneRequest) -> MarkDoneResponse:
    updated = db.mark_action_item_done(action_item_id, payload.done)
    if not updated:
        raise HTTPException(status_code=404, detail="Action item not found")
    return MarkDoneResponse(id=action_item_id, done=payload.done)
