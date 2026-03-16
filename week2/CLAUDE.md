# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands should be run from the `CS146S/hw/` parent directory (where `pyproject.toml` lives).

```bash
# Run the app
poetry run uvicorn week2.app.main:app --reload

# Run tests
poetry run pytest

# Run a single test
poetry run pytest week2/tests/test_extract.py::test_extract_bullets_and_checkboxes

# Format code
poetry run black .

# Lint
poetry run ruff check .
poetry run ruff check --fix .
```

Activate the conda environment first if needed: `conda activate cs146s`

## Architecture

This is a FastAPI app that extracts action items from free-form notes using either heuristics or an LLM (Ollama).

**Request flow:**
1. Frontend (`frontend/index.html`) sends JSON to FastAPI
2. Routers (`app/routers/`) handle HTTP endpoints and delegate to services/db
3. `app/services/extract.py` contains extraction logic (heuristic + TODO: LLM via Ollama)
4. `app/db.py` is a raw SQLite layer (no ORM despite SQLAlchemy being installed) with two tables: `notes` and `action_items`

**Key design notes:**
- The app module is `week2.app.main:app` (module path matters because pyproject.toml is one level up)
- `db.py` uses `row_factory` for named column access; the DB file is at `data/app.db` relative to the week2 directory
- Routers use `Dict[str, Any]` return types — there are no Pydantic response models yet (improvement opportunity per assignment TODO 3)
- `extract.py` imports `ollama` but the LLM function is not yet implemented (TODO 1)

## Assignment TODOs

This is a CS146S Week 2 homework assignment. Remaining work:
1. **TODO 1** — Implement `extract_action_items_llm()` in `app/services/extract.py` using Ollama structured outputs (JSON)
2. **TODO 2** — Expand `tests/test_extract.py` to cover LLM extraction across multiple input types
3. **TODO 3** — Refactor: add Pydantic schemas, improve DB layer, add app lifecycle/config management
4. **TODO 4** — Add `/action-items/extract-llm` endpoint and "Extract LLM" + "List Notes" buttons to frontend
5. **TODO 5** — Auto-generate `README.md` from codebase using AI
