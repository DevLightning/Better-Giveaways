import asyncio
import random
from datetime import timedelta
from typing import Optional, List

import discord  # type: ignore
from discord import utils as discord_utils
from discord.ext import tasks, vbu  # type: ignore

from . import utils


class Tasks(vbu.Cog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._giveaway_checker.start()

    @tasks.loop(seconds=5.0)
    async def _giveaway_checker(self) -> None:
        """
        The giveaway checker loop. This loop checks for active giveaways and
        ends them if necessary.
        """

        # Bot needs  to be ready for some internal operations to be
        # performed, namely cache-related ones like `bot.get_channel`.
        if not self.bot.is_ready():
            return

        async with vbu.DatabaseConnection() as db:
            giveaways = await utils.get_giveaways(db)
            if giveaways is not None:
                for giveaway in giveaways:
                    if giveaway.ends_at <= discord_utils.utcnow():
                        await giveaway.end(db, self.bot)


def setup(bot: vbu.Bot):
    x = Tasks(bot)
    bot.add_cog(x)
