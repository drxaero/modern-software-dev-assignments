from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import db
from ..schemas import NoteCreate, NoteResponse

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteResponse, status_code=201)
def create_note(payload: NoteCreate) -> NoteResponse:
    note_id = db.insert_note(payload.content)
    note = db.get_note(note_id)
    return NoteResponse(**note)


@router.get("", response_model=list[NoteResponse])
def list_notes() -> list[NoteResponse]:
    return [NoteResponse(**row) for row in db.list_notes()]


@router.get("/{note_id}", response_model=NoteResponse)
def get_single_note(note_id: int) -> NoteResponse:
    note = db.get_note(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteResponse(**note)
