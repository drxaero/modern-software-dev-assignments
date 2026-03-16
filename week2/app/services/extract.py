from __future__ import annotations

import os
import re
from typing import List
import json
from typing import Any
from dotenv import load_dotenv

from app.ollama_client import call_api

load_dotenv()

BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False


def __extract_action_items(text: str) -> List[str]:
    lines = text.splitlines()
    extracted: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            # Trim common checkbox markers
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            extracted.append(cleaned)
    # Fallback: if nothing matched, heuristically split into sentences and pick imperative-like ones
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters


_ACTION_ITEMS_SCHEMA = {
    "type": "object",
    "properties": {
        "action_items": {
            "type": "array",
            "items": {"type": "string"},
        }
    },
    "required": ["action_items"],
}

_SYS_PROMPT = (
    "You are an assistant that extracts action items from notes. "
    "Return a JSON object with an 'action_items' key containing an array of strings. "
    "Each string must be copied VERBATIM from the input — strip only leading bullet markers "
    "(-, *, •, digits followed by a period) and checkbox markers ([ ]) from the start, "
    "but otherwise preserve the exact original wording, casing, and punctuation. "
    "Do not rephrase, summarize, or add words. "
    "If there are no action items, return an empty array."
)


def __extract_action_items_llm(text: str) -> list[str]:
    raw = call_api(
        model="llama3.1:8b",
        sys_prompt=_SYS_PROMPT,
        usr_prompt=text,
        temperature=0.0,
        format=_ACTION_ITEMS_SCHEMA,
    )
    data = json.loads(raw)
    items = data.get("action_items", [])
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def extract_action_items(text: str) -> list[str]:
    if text.strip() == "":
        return []
    return __extract_action_items_llm(text)
