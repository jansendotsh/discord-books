"""Runtime configuration read from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is required but not set")
    return value


@dataclass(frozen=True)
class Config:
    discord_token: str
    database_path: str
    book_channel_id: int
    book_role_id: int
    admin_ids: frozenset[int]

    @classmethod
    def from_env(cls) -> "Config":
        admin_env = os.getenv("ADMIN_IDS", "")
        admins = frozenset(
            int(id.strip())
            for id in admin_env.split(",")
            if id.strip().isdecimal()
        )
        return cls(
            discord_token=_required("DISCORD_TOKEN"),
            database_path=os.getenv("DATABASE_PATH", "data/bookbot.db"),
            book_channel_id=int(_required("BOOK_CHANNEL_ID")),
            book_role_id=int(_required("BOOK_ROLE_ID")),
            admin_ids=admins,
        )
