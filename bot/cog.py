"""Book club commands as a discord.py extension cog."""

from __future__ import annotations

import random

import discord
from discord import app_commands
from discord.ext import commands

from .db import Database
from .embeds import links_field, make_embed


class BookClubCog(commands.Cog):
    """All book-club slash commands."""

    def __init__(self, bot: commands.Bot, db: Database) -> None:
        self.bot = bot
        self.db = db

    # --- guard helpers -------------------------------------------------

    def _channel_check(self, interaction: discord.Interaction) -> bool:
        return interaction.channel_id == self.bot.config.book_channel_id

    def _admin_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id in self.bot.config.admin_ids

    async def _ensure_channel(
        self, interaction: discord.Interaction
    ) -> bool:
        if not self._channel_check(interaction):
            await interaction.response.send_message(
                f"This command belongs in <#{self.bot.config.book_channel_id}>.",
                ephemeral=True,
            )
            return False
        return True

    async def _ensure_admin(
        self, interaction: discord.Interaction
    ) -> bool:
        if not self._admin_check(interaction):
            await interaction.response.send_message(
                "You don't have permission to run this command.",
                ephemeral=True,
            )
            return False
        return True

    # --- commands ------------------------------------------------------

    @app_commands.command(
        name="current",
        description="Show the current book with links.",
    )
    async def current(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_channel(interaction):
            return
        book = await self.db.current_book()
        if not book:
            await interaction.response.send_message(
                "No current book is set.", ephemeral=True
            )
            return
        embed = make_embed(
            "Current Book",
            f"The current book is **{book['title']}** by **{book['author']}**.\n\n"
            f"{links_field(book)}",
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="next",
        description="Show the next upcoming book.",
    )
    async def next_(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_channel(interaction):
            return
        upcoming = await self.db.list_upcoming()
        if not upcoming:
            await interaction.response.send_message(
                "No upcoming books. Use `/add` to add one.",
                ephemeral=True,
            )
            return
        book = upcoming[0]
        embed = make_embed(
            "Next Book",
            f"The next book is **{book['title']}** by **{book['author']}**.\n\n"
            f"{links_field(book)}",
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="past",
        description="Show recent books (including current).",
    )
    @app_commands.describe(count="Number of books to show (1–25)")
    async def past(
        self, interaction: discord.Interaction, count: int = 5
    ) -> None:
        if not await self._ensure_channel(interaction):
            return
        count = max(1, min(count, 25))
        books = await self.db.list_past()
        if not books:
            await interaction.response.send_message(
                "No past books yet.", ephemeral=True
            )
            return
        books = books[:count]
        embed = make_embed(
            "Past Books",
            f"Showing the {len(books)} most recent book(s):",
        )
        for book in books:
            embed.add_field(
                name=f"{book['title']} by {book['author']}",
                value=links_field(book),
                inline=False,
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="add",
        description="Add a book to the upcoming list.",
    )
    @app_commands.describe(
        title="Book title",
        author="Author name",
        goodreads="Optional Goodreads link",
        bookshop="Optional BookShop link",
        ebook="Optional eBook link",
        audiobook="Optional audiobook link",
    )
    async def add(
        self,
        interaction: discord.Interaction,
        title: str,
        author: str,
        goodreads: str | None = None,
        bookshop: str | None = None,
        ebook: str | None = None,
        audiobook: str | None = None,
    ) -> None:
        if not await self._ensure_channel(interaction):
            return
        await self.db.add_upcoming(
            title, author, goodreads, bookshop, ebook, audiobook
        )
        embed = make_embed(
            "Added Book",
            f"Added **{title}** by **{author}** to the upcoming list.",
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="swap",
        description="(Admin) Promote the next book to current, clear progress.",
    )
    async def swap(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_channel(interaction):
            return
        if not await self._ensure_admin(interaction):
            return

        promoted = await self.db.remove_first_upcoming()
        if not promoted:
            await interaction.response.send_message(
                "No upcoming books to promote.", ephemeral=True
            )
            return
        await self.db.add_past(
            promoted["title"],
            promoted["author"],
            promoted.get("goodreads"),
            promoted.get("bookshop"),
            promoted.get("ebook"),
            promoted.get("audiobook"),
        )
        await self.db.clear_progress()

        current = await self.db.current_book()
        description = (
            f"<@&{self.bot.config.book_role_id}> It's time to start the next book!\n\n"
            f"We're now reading **{current['title']}** by **{current['author']}**.\n\n"
            f"{links_field(current)}"
        )
        embed = make_embed("New Book Started", description)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="update",
        description="Update your reading progress (page count or percentage).",
    )
    @app_commands.describe(
        value="Pages read (e.g. 120) or percentage (e.g. 42%)",
        total="Total pages in your edition (to convert pages to %)",
    )
    async def update(
        self,
        interaction: discord.Interaction,
        value: str,
        total: int | None = None,
    ) -> None:
        if not await self._ensure_channel(interaction):
            return
        current = await self.db.current_book()
        if not current:
            await interaction.response.send_message(
                "No current book is set.", ephemeral=True
            )
            return

        percent = self._parse_progress(value, total)
        if percent is None:
            await interaction.response.send_message(
                "Provide a page count (e.g. `120`) or a percentage (e.g. `42%`).",
                ephemeral=True,
            )
            return

        await self.db.upsert_progress(interaction.user.name, percent)
        embed = make_embed(
            "Progress Update",
            f"Nice, {interaction.user.name}. Your progress for "
            f"**{current['title']}** by **{current['author']}** "
            f"is now **{percent}%** :book:",
        )
        await interaction.response.send_message(embed=embed)

    @staticmethod
    def _parse_progress(value: str, total: int | None) -> int | None:
        value = value.strip()
        if value.endswith("%"):
            try:
                pct = int(value[:-1])
            except ValueError:
                return None
            return max(0, min(pct, 100))
        if total is not None and total > 0:
            try:
                pages = int(value)
            except ValueError:
                return None
            return max(0, min(round(pages / total * 100), 100))
        return None

    @app_commands.command(
        name="progress",
        description="Show everyone's progress on the current book.",
    )
    async def progress(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_channel(interaction):
            return
        current = await self.db.current_book()
        if not current:
            await interaction.response.send_message(
                "No current book is set.", ephemeral=True
            )
            return
        entries = await self.db.list_progress()
        if not entries:
            embed = make_embed(
                "Book Progress",
                f"No one has logged progress for **{current['title']}** yet.",
            )
            await interaction.response.send_message(embed=embed)
            return

        lines: list[str] = []
        for entry in entries:
            pct = entry["percent"]
            filled = pct // 10
            bar = "█" * filled + "░" * (10 - filled)
            lines.append(f"**{entry['username']}** — {bar} {pct}%")

        embed = make_embed(
            "Book Progress",
            f"Progress for **{current['title']}** by **{current['author']}**:\n\n"
            + "\n".join(lines),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="random",
        description="Pick a random upcoming book.",
    )
    async def random_pick(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_channel(interaction):
            return
        upcoming = await self.db.list_upcoming()
        if not upcoming:
            await interaction.response.send_message(
                "No upcoming books to pick from.", ephemeral=True
            )
            return
        book = random.choice(upcoming)
        embed = make_embed(
            "Random Pick",
            f"How about **{book['title']}** by **{book['author']}**?",
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BookClubCog(bot, bot.db))
