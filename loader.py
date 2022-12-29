import pathlib
import os
import logging

import discord
import discord.ext.commands.errors


class Handler():
    def __init__(self, client: discord.Client):
        self._client = client

        self._cwd = pathlib.Path.cwd()
        self.name = os.path.basename(__file__)

        self.logger = logging.getLogger()

    async def cog_auto_loader(self, reload=False):
        """This will load all Cogs inside of the cogs folder."""
        path = f'cogs'  # This gets us to the folder for the module specific scripts to load via the cog.
        try:
            cog_file_list = pathlib.Path.joinpath(self._cwd, 'cogs').iterdir()
            for script in cog_file_list:
                if script.name.endswith('.py'):
                    cog = f'{path}.{script.name[:-3]}'

                    try:
                        if reload:
                            await self._client.reload_extension(cog)
                        else:
                            await self._client.load_extension(cog)

                        self.logger.info(
                            f'**SUCCESS** {self.name} Loading Cog **{cog}**')

                    except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                        continue

        except FileNotFoundError as e:
            self.logger.error(f'**ERROR** Loading Cog ** - File Not Found {e}')
