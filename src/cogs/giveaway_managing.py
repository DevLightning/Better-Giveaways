import asyncio
import random

import discord  # type: ignore
from discord.ext import commands, vbu  # type: ignore


class PingCommand(vbu.Cog):
    @commands.command(name="create-giveaway", help="Create a new giveaway!")
    @commands.is_slash_command()
    async def _create_giveaway_command(self, ctx: vbu.SlashContext) -> None:
        """
        The callback for the create-giveaway bot command. This command creates a new giveaway.

        Parameters
        ----------
        ctx : vbu.SlashContext
            The context for the command.

        Returns
        -------
        None
        """

        await ctx.interaction.response.send_message("Test!")


def setup(bot: vbu.Bot):
    x = PingCommand(bot)
    bot.add_cog(x)
