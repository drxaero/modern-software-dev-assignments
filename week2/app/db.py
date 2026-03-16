from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "app.db"


# ── Row helpers ─────────────────────────────────────────────────────────────

def _note_row(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "content": row["content"], "created_at": row["created_at"]}


def _action_item_row(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "note_id": row["note_id"],
        "text": row["text"],
        "done": bool(row["done"]),
        "created_at": row["created_at"],
    }


# ── Connection ───────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# ── Schema init ──────────────────────────────────────────────────────────────

def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                content    TEXT    NOT NULL,
                created_at TEXT    DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS action_items (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id    INTEGER,
                text       TEXT    NOT NULL,
                done       INTEGER DEFAULT 0,
                created_at TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (note_id) REFERENCES notes(id)
            );
            """
        )


# ── Notes ────────────────────────────────────────────────────────────────────

def insert_note(content: str) -> int:
    with get_connection() as connection:
        cursor = connection.execute("INSERT INTO notes (content) VALUES (?)", (content,))
        return int(cursor.lastrowid)


def list_notes() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, content, created_at FROM notes ORDER BY id DESC"
        ).fetchall()
        return [_note_row(r) for r in rows]


def get_note(note_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, content, created_at FROM notes WHERE id = ?", (note_id,)
        ).fetchone()
        return _note_row(row) if row else None


# ── Action items ─────────────────────────────────────────────────────────────

def insert_action_items(items: list[str], note_id: int | None = None) -> list[int]:
    with get_connection() as connection:
        ids: list[int] = []
        for item in items:
            cursor = connection.execute(
                "INSERT INTO action_items (note_id, text) VALUES (?, ?)", (note_id, item)
            )
            ids.append(int(cursor.lastrowid))
        return ids


def list_action_items(note_id: int | None = None) -> list[dict]:
    with get_connection() as connection:
        if note_id is None:
            rows = connection.execute(
                "SELECT id, note_id, text, done, created_at FROM action_items ORDER BY id DESC"
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT id, note_id, text, done, created_at FROM action_items"
                " WHERE note_id = ? ORDER BY id DESC",
                (note_id,),
            ).fetchall()
        return [_action_item_row(r) for r in rows]


def mark_action_item_done(action_item_id: int, done: bool) -> bool:
    """Returns True if a row was updated, False if the id did not exist."""
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE action_items SET done = ? WHERE id = ?",
            (1 if done else 0, action_item_id),
        )
        return cursor.rowcount > 0
