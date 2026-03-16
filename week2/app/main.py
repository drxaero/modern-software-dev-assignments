from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .db import init_db
from .routers import action_items, notes


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Action Item Extractor", lifespan=lifespan)

app.include_router(notes.router)
app.include_router(action_items.router)

_frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/static", StaticFiles(directory=str(_frontend_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (_frontend_dir / "index.html").read_text(encoding="utf-8")
