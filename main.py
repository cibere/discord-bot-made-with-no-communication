import discord
from discord.ext import commands

import config
import logging

logger = logging.getLogger(__name__)

extensions = (
    'cogs.games'
)

class Bot(commands.Bot):

    def __init__(self) -> None:
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, replied_user=False)

        super().__init__(
            intents=intents,
            allowed_mentions=allowed_mentions,
            command_prefix=self.get_prefix
        )

    async def get_prefix(self, message: discord.Message):
        return ['!', '?']

    async def setup_hook(self) -> None:
        
        for ext in extensions:
            try:
                await self.load_extension(ext)
            except Exception as e:
                logger.error(f'Failed to load extention: {e}')

bot = Bot()
bot.run(config.token)
