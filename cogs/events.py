from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from main import Bot


class Events(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.ERRORS_TO_IGNORE = (commands.CommandNotFound,)

    def cog_load(self):
        tree = self.bot.tree
        tree.on_error = self.on_app_command_error

    def cog_unload(self):
        tree = self.bot.tree
        tree.on_error = tree.__class__.on_error  # type: ignore

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, self.ERRORS_TO_IGNORE):
            return
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("Oh no, seems you do not have any authority. Not even enough to run this stupid command 🤣")
        else:
            await ctx.send(f"Uh oh. An error has occured\n```py{error}\n```")
            raise error

    async def on_app_command_error(self, inter: discord.Interaction, error: Exception):
        if inter.response.is_done():
            send = inter.followup.send
        else:
            send = inter.response.send_message

        if isinstance(error, self.ERRORS_TO_IGNORE):
            return
        else:
            await send(f"Uh oh. An error has occured\n```py{error}\n```")
            raise error


async def setup(bot: Bot):
    await bot.add_cog(Events(bot))
