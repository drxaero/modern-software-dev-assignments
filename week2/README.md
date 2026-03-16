# Action Item Extractor

A FastAPI application that extracts action items from free-form notes using an LLM (Ollama).

## Overview

Paste meeting notes or free-form text into the web interface — the app extracts actionable items using a local LLM and persists them in SQLite.

## Setup

```bash
# Activate the conda environment
conda activate cs146s

# Run the app (from CS146S/hw/ parent directory)
poetry run uvicorn week2.app.main:app --reload
```

Open `http://127.0.0.1:8000/` in your browser.

**Requirements:**
- An Ollama server running at `http://10.248.36.193:11434` with `llama3.1:8b` available
- Python >= 3.10 with Poetry

## Project Structure

```
week2/
├── app/
│   ├── main.py              # FastAPI entry point, lifespan, static mounts
│   ├── db.py                # Raw SQLite layer (notes + action_items tables)
│   ├── schemas.py           # Pydantic request/response models
│   ├── ollama_client.py     # HTTP client for Ollama /api/generate
│   ├── routers/
│   │   ├── notes.py         # CRUD for notes
│   │   └── action_items.py  # Extraction + action item management
│   └── services/
│       └── extract.py       # Extraction logic (heuristic + LLM)
├── frontend/
│   └── index.html           # Vanilla JS single-page interface
├── tests/
│   └── test_extract.py      # pytest unit tests for extraction
└── data/
    └── app.db               # SQLite database (auto-created on first run)
```

## API Endpoints

### Notes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/notes` | Create a note |
| `GET` | `/notes` | List all notes |
| `GET` | `/notes/{id}` | Get a single note |

### Action Items

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/action-items/extract` | Extract action items from text |
| `GET` | `/action-items` | List action items (optionally filter by `?note_id=`) |
| `POST` | `/action-items/{id}/done` | Mark an item done/undone |

#### Extract request body

```json
{
  "text": "Meeting notes here...",
  "save_note": true
}
```

#### Extract response

```json
{
  "note_id": 1,
  "items": [
    { "id": 1, "text": "Send follow-up email" }
  ]
}
```

## Database Schema

```sql
CREATE TABLE notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    content    TEXT    NOT NULL,
    created_at TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE action_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id    INTEGER REFERENCES notes(id),
    text       TEXT    NOT NULL,
    done       INTEGER DEFAULT 0,
    created_at TEXT    DEFAULT (datetime('now'))
);
```

## Extraction Logic

**LLM path** (`extract_action_items_llm`): Sends text to `llama3.1:8b` via Ollama's `/api/generate` with a structured JSON output schema. The model returns action items verbatim from the input. Results are deduplicated case-insensitively.

**Heuristic path** (available but not the default): Matches bullet/numbered patterns, keyword prefixes (`todo:`, `action:`, `next:`), checkbox markers (`[ ]`, `[todo]`), and imperative sentence starters as a fallback.

## Development

```bash
# Run all tests
poetry run pytest

# Run a specific test
poetry run pytest week2/tests/test_extract.py::test_extract_bullets_and_checkboxes

# Format
poetry run black .

# Lint
poetry run ruff check .
poetry run ruff check --fix .
```
