import discord
from discord.ext import commands

import config

class Bot(commands.Bot):
    
    def __init__(self) -> None:
        import logger
        import logging
        logger.init()
        self._logger = logging.getLogger()
        
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
        import loader
        self._handler = loader.Handler(self)
        #Iterates through all the .py files inside the `cogs` folder and attempts to load them.
        await self._handler.cog_auto_loader()

    async def on_ready(self):
        self._logger.info('discord-bot-made-with-no-communication is ready...')

bot = Bot()
bot.run(config.token)
