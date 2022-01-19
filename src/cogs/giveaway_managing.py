import asyncio
import random
from datetime import timedelta
from typing import Optional, List

import discord  # type: ignore
from discord import utils as discord_utils  # type: ignore
from discord.ext import commands, vbu  # type: ignore

from . import utils


class GiveawayManaging(vbu.Cog):
    @commands.command(
        name="create-giveaway",
        help="Create a new giveaway!",
    )
    @commands.is_slash_command()
    async def _create_giveaway_command(
        self,
        ctx: vbu.SlashContext,
        seconds: int = 60,
        role: Optional[discord.Role] = None,
    ) -> None:
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
        giveaway_reward = utils.GiveawayRoleReward(role.id) if role else None
        giveaway_ends_at = discord_utils.utcnow() + timedelta(seconds=seconds)
        giveaway_message = await ctx.channel.send(
            "Created a giveaway\nEnding: "
            f" {discord_utils.format_dt(giveaway_ends_at, style='R')}!"
            f" Reward: {giveaway_reward or 'nothing lol'}"
        )
        await giveaway_message.add_reaction("🎉")
        giveaway = utils.Giveaway(
            ctx.guild.id,
            ctx.channel.id,
            giveaway_message.id,
            giveaway_ends_at,
        )

        if giveaway_reward:
            giveaway.role_rewards = [giveaway_reward]

        async with vbu.DatabaseConnection() as db:
            await giveaway.update(db)

    @commands.command(
        name="active-giveaways",
        help="View all active giveaways in the current server.",
    )
    @commands.is_slash_command()
    @commands.guild_only()
    async def _active_giveaways_command(
        self, ctx: vbu.SlashContext, channel: Optional[discord.TextChannel] = None
    ) -> None:
        """
        View all active giveaways in the current server.

        Parameters
        ----------
        ctx : vbu.SlashContext
            The context for the command.
        channel : discord.TextChannel
            The channel to view the active giveaways in.

        Returns
        -------
        None
        """

        async with vbu.DatabaseConnection() as db:
            giveaways = (
                await utils.get_giveaways(db, channel=channel)
                if channel is not None
                else await utils.get_giveaways(db, guild=ctx.guild)
            )

        if not giveaways:
            if channel is None:
                await ctx.interaction.response.send_message(
                    "No active giveaways in this server :pensive:"
                )
            else:
                if channel == ctx.channel:
                    await ctx.interaction.response.send_message(
                        "No active giveaways in this channel :pensive:"
                    )
                else:
                    await ctx.interaction.response.send_message(
                        f"No active giveaways in {channel.mention} :pensive:"
                    )
            return

        # Paginate the active giveaways.
        def formatter(
            menu: vbu.Paginator, giveaways: List[utils.Giveaway]
        ) -> discord.Embed:
            with vbu.Embed(
                title="Active Giveaways",
                description=f"All active giveaways in **{channel.mention}**."
                if channel is not None
                else f"All active giveaways in **{ctx.guild}**.",
                colour=discord.colour.Colour.green(),
            ) as embed:
                for giveaway in giveaways:
                    embed.add_field(
                        f"{giveaway.role_rewards}",
                        f"[Jump!]({giveaway.message_url})  Ending: {discord_utils.format_dt(giveaway.ends_at, style='R')}",
                        inline=False,
                    )
                embed.set_footer(f"Page {menu.current_page + 1}/{menu.max_pages}")
            return embed

        paginator = vbu.Paginator(giveaways, per_page=5, formatter=formatter)
        await paginator.start(ctx)


def setup(bot: vbu.Bot):
    x = GiveawayManaging(bot)
    bot.add_cog(x)
