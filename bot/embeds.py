"""Embed helpers for consistent styling across all commands."""

from __future__ import annotations

import discord

BOOK_ICON = "https://s.jnsn.link/book/book.png"
BOOKMARK_ICON = "https://s.jnsn.link/book/bookmark.png"
EMBED_COLOR = discord.Color(0x8FD7C3)

LINK_LABELS = ("Goodreads", "BookShop", "eBook", "Audiobook")
LINK_KEYS = ("goodreads", "bookshop", "ebook", "audiobook")


def make_embed(title: str, description: str = "") -> discord.Embed:
    embed = discord.Embed(
        description=description,
        color=EMBED_COLOR,
    )
    embed.set_author(name=title, icon_url=BOOK_ICON)
    embed.set_thumbnail(url=BOOKMARK_ICON)
    return embed


def links_field(book: dict) -> str:
    parts: list[str] = []
    for label, key in zip(LINK_LABELS, LINK_KEYS):
        value = book.get(key)
        if value:
            parts.append(f"_ {label}: _ {value}")
    return "\n".join(parts) if parts else "No links available."
