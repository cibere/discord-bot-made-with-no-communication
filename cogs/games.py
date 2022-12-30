from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from main import Bot


class Games(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot


async def setup(bot: Bot):
    await bot.add_cog(Games(bot))
