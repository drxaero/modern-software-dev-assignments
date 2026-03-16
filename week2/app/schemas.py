from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, field_validator


# ── Notes ──────────────────────────────────────────────────────────────────


class NoteCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("content must not be empty")
        return v


class NoteResponse(BaseModel):
    id: int
    content: str
    created_at: str


# ── Action items ────────────────────────────────────────────────────────────


class ExtractRequest(BaseModel):
    text: str
    save_note: bool = False

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("text must not be empty")
        return v


class ExtractedItem(BaseModel):
    id: int
    text: str


class ExtractResponse(BaseModel):
    note_id: Optional[int]
    items: list[ExtractedItem]


class ActionItemResponse(BaseModel):
    id: int
    note_id: Optional[int]
    text: str
    done: bool
    created_at: str


class MarkDoneRequest(BaseModel):
    done: bool = True


class MarkDoneResponse(BaseModel):
    id: int
    done: bool
