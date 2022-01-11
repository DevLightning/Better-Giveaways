import asyncio
import random
from datetime import datetime, timedelta

import discord  # type: ignore
from discord import utils as discord_utils  # type: ignore
from discord.ext import commands, vbu  # type: ignore

import utils


class GiveawayManaging(vbu.Cog):
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

        await ctx.interaction.response.send_message("Creating a testing giveaway!")

        # Create a testing giveaway.
        giveaway_reward = "1x Classic Nitro"
        giveaway_ends_at = datetime.utcnow() + timedelta(hours=1)
        giveaway_message = await ctx.channel.send(
            "Proto giveaway message! Ending at"
            f" {discord_utils.format_dt(giveaway_ends_at, style='F')}!"
            f" Reward: {giveaway_reward}"
        )
        giveaway = utils.Giveaway(
            ctx.guild.id,
            ctx.channel.id,
            giveaway_message.id,
            giveaway_ends_at,
            giveaway_reward,
        )

        async with vbu.DatabaseConnection() as db:
            await giveaway.update(db)


def setup(bot: vbu.Bot):
    x = GiveawayManaging(bot)
    bot.add_cog(x)
