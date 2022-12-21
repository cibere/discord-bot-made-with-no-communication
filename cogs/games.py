import discord
from discord.ext import commands

from main import Bot

async def setup(bot: Bot):
    await bot.add_cog(Games(bot))

class Games(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot