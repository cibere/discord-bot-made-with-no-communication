from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands as ap
from discord import ui
from discord.ext import commands

if TYPE_CHECKING:
    from main import Bot


class Player:
    member: discord.Member
    choice: Optional[str]
    id: int
    mention: str

    def __init__(self, mem: discord.Member, /):
        self.member = mem
        self.choice = None
        self.id = mem.id
        self.mention = mem.mention

    def __repr__(self) -> str:
        return f"<Player id={self.member.id}>"


class Handler(ui.View):
    message: discord.Message
    p1: Player
    p2: Player

    def __init__(self, p1: discord.Member, p2: discord.Member, cmd_id: int):
        super().__init__()
        self.p1 = Player(p1)
        self.p2 = Player(p2)
        self.cmd_id = cmd_id

        self.authorized = [self.p1.id, self.p2.id]

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True  # type: ignore

        await self.message.edit(
            content="This game timed out",
            embed=None,
            view=None,
        )
        return await super().on_timeout()

    async def interaction_check(self, inter: discord.Interaction) -> bool:
        if inter.user.id not in self.authorized:
            await inter.response.send_message("Oh no... its so sad... you are not allowed to play", ephemeral=True)
            return False
        elif inter.user.id == self.p1.id:
            if self.p1.choice:
                await inter.response.send_message(
                    f"You have already chosen `{self.p1.choice}`. Please wait for {self.p2.mention} to make their choice.",
                    ephemeral=True,
                )
                return False
        elif inter.user.id == self.p2.id:
            if self.p2.choice:
                await inter.response.send_message(
                    f"You have already chosen `{self.p2.choice}`. Please wait for {self.p1.mention} to make their choice.",
                    ephemeral=True,
                )
                return False

        return True

    async def choose_winner(self, inter: discord.Interaction) -> None:
        p1c = self.p1.choice
        p2c = self.p2.choice
        assert isinstance(p1c, str)
        assert isinstance(p2c, str)

        mapping: dict[tuple[str, str], str] = {
            # rock
            ("rock", "scissors"): "{0}'s rock crushes {1}'s scissors!",
            ("rock", "paper"): "{1}'s paper beats rock!",
            ("rock", "rock"): "{0} and {1} both picked rock, and tied.",
            # paper
            ("paper", "scissors"): "{1}'s scissors cuts {0}'s paper!",
            ("paper", "paper"): "{0} and {1} both picked paper, and tied.",
            ("paper", "rock"): "{1}'s paper beats rock!",
            # scissors
            ("scissors", "scissors"): "{0} and {1} both picked scissors, and tied.",
            ("scissors", "paper"): "{0}'s scissors cuts {1}'s paper in half!",
            ("scissors", "rock"): "{1}'s rock crushes {0}'s scissors!",
        }

        self.btn_rock.disabled = True
        self.btn_paper.disabled = True
        self.btn_knife.disabled = True

        await inter.response.edit_message(content=mapping[(p1c, p2c)].format(self.p1.mention, self.p2.mention), view=self)
        self.stop()

    async def callback(self, inter: discord.Interaction, choice: str) -> None:
        if self.p1.id == inter.user.id:
            self.p1.choice = choice
            other_player = self.p2
        else:
            self.p2.choice = choice
            other_player = self.p1

        if self.p1.choice and self.p2.choice:
            await self.choose_winner(inter)
        else:
            await inter.response.send_message(
                f"Choice chosen. Waiting for {other_player.mention} to choose...", ephemeral=True
            )

    @ui.button(emoji='🪨')
    async def btn_rock(self, inter: discord.Interaction, btn: ui.Button):
        await self.callback(inter, "rock")

    @ui.button(emoji='🧻')
    async def btn_paper(self, inter: discord.Interaction, btn: ui.Button):
        await self.callback(inter, "paper")

    @ui.button(emoji='✂️')
    async def btn_knife(self, inter: discord.Interaction, btn: ui.Button):
        await self.callback(inter, "scissors")


class RPS(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @ap.command(name="rps", description="lets you play rps")
    @ap.guild_only()
    async def cmd_rps(self, inter: discord.Interaction, target: discord.Member):
        assert isinstance(inter.user, discord.Member)
        if target.bot:
            return await inter.response.send_message("You can not play against a bot", ephemeral=True)
        elif target.id == inter.user.id:
            return await inter.response.send_message("You can not play against yourself", ephemeral=True)

        id_ = int(inter.data["id"])  # type: ignore
        view = Handler(inter.user, target, id_)
        await inter.response.send_message(
            view=view,
            content=f"{target.mention}, {inter.user.mention} has invited you to play a game of rock, paper, scissors!",
        )
        view.message = await inter.original_response()


async def setup(bot: Bot):
    await bot.add_cog(RPS(bot))
