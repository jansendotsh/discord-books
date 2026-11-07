"""Entry point: python -m bot."""

from __future__ import annotations

import asyncio
import logging

from .bot import build_bot


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    bot = build_bot()
    asyncio.run(bot.run(bot.config.discord_token))


if __name__ == "__main__":
    main()
