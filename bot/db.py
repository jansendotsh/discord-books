"""Async SQLite persistence layer for the book club bot."""

from __future__ import annotations

from typing import Any

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS upcoming (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    author      TEXT NOT NULL,
    goodreads   TEXT,
    bookshop    TEXT,
    ebook       TEXT,
    audiobook   TEXT
);

CREATE TABLE IF NOT EXISTS past (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    author      TEXT NOT NULL,
    goodreads   TEXT,
    bookshop    TEXT,
    ebook       TEXT,
    audiobook   TEXT
);

CREATE TABLE IF NOT EXISTS progress (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT NOT NULL UNIQUE,
    percent     INTEGER NOT NULL DEFAULT 0
);
"""


class Database:
    """Thin wrapper around an aiosqlite connection."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA)
        await self._db.commit()

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    @property
    def db(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Database not connected; call connect() first")
        return self._db

    # --- upcoming ---
    async def list_upcoming(self) -> list[dict[str, Any]]:
        async with self.db.execute(
            "SELECT * FROM upcoming ORDER BY id"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def add_upcoming(
        self,
        title: str,
        author: str,
        goodreads: str | None = None,
        bookshop: str | None = None,
        ebook: str | None = None,
        audiobook: str | None = None,
    ) -> None:
        await self.db.execute(
            """
            INSERT INTO upcoming (title, author, goodreads, bookshop, ebook, audiobook)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, author, goodreads, bookshop, ebook, audiobook),
        )
        await self.db.commit()

    async def remove_upcoming(self, row_id: int) -> None:
        await self.db.execute("DELETE FROM upcoming WHERE id = ?", (row_id,))
        await self.db.commit()

    async def remove_first_upcoming(self) -> dict[str, Any] | None:
        async with self.db.execute(
            "SELECT * FROM upcoming ORDER BY id LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        await self.db.execute("DELETE FROM upcoming WHERE id = ?", (row["id"],))
        await self.db.commit()
        return dict(row)

    # --- past ---
    async def list_past(self) -> list[dict[str, Any]]:
        async with self.db.execute(
            "SELECT * FROM past ORDER BY id DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def add_past(
        self,
        title: str,
        author: str,
        goodreads: str | None = None,
        bookshop: str | None = None,
        ebook: str | None = None,
        audiobook: str | None = None,
    ) -> None:
        await self.db.execute(
            """
            INSERT INTO past (title, author, goodreads, bookshop, ebook, audiobook)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, author, goodreads, bookshop, ebook, audiobook),
        )
        await self.db.commit()

    async def current_book(self) -> dict[str, Any] | None:
        async with self.db.execute(
            "SELECT * FROM past ORDER BY id DESC LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    # --- progress ---
    async def list_progress(self) -> list[dict[str, Any]]:
        async with self.db.execute(
            "SELECT * FROM progress ORDER BY percent DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def upsert_progress(self, username: str, percent: int) -> None:
        await self.db.execute(
            """
            INSERT INTO progress (username, percent) VALUES (?, ?)
            ON CONFLICT(username) DO UPDATE SET percent = excluded.percent
            """,
            (username, percent),
        )
        await self.db.commit()

    async def clear_progress(self) -> None:
        await self.db.execute("DELETE FROM progress")
        await self.db.commit()
