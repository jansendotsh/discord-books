"""Bot client and lifecycle wiring."""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from .config import Config
from .db import Database

log = logging.getLogger("bookbot")


class BookBot(commands.Bot):
    """commands.Bot subclass carrying config and a db handle."""

    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        intents.message_content = False  # slash commands only
        super().__init__(
            command_prefix=commands.when_mentioned_or("b!"),
            intents=intents,
        )
        self.config = config
        self.db = Database(config.database_path)

    async def setup_hook(self) -> None:
        await self.db.connect()
        await self.load_extension("bot.cog")
        await self.tree.sync()

    async def on_ready(self) -> None:
        log.info("Logged in as %s (id=%s)", self.user, self.user.id)

    async def close(self) -> None:
        await self.db.close()
        await super().close()


def build_bot() -> BookBot:
    return BookBot(Config.from_env())
