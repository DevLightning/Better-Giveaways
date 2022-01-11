import asyncio
import random

import discord  # type: ignore
from discord.ext import commands, vbu  # type: ignore


class PingCommand(vbu.Cog):
    @commands.command(name="ping")
    @commands.is_slash_command()
    async def _ping_command(self, ctx: vbu.SlashContext) -> None:
        """
        An example ping command.
        """

        await ctx.interaction.response.send_message("Pong!")

    @commands.command(name="fast-ping")
    @commands.is_slash_command()
    async def _fast_ping_command(self, ctx: vbu.SlashContext) -> None:
        """
        Fast ping! Quickly press the green button.
        """

        # NOTE: keep `rows` and `columns` lower than the 5, since that's the
        #       maxiumum.
        rows = 5
        columns = 5
        pong_coordinates = random.randrange(0, rows), random.randrange(0, columns)
        components = discord.ui.MessageComponents()

        # Add action rows for every row and buttons for every column.
        for y_index in range(rows):
            action_row = discord.ui.ActionRow()
            for x_index in range(columns):

                # Special button at the pong coordinates.
                if (x_index, y_index) == pong_coordinates:
                    button = discord.ui.Button(
                        label="Pong!",
                        custom_id=f"PONG_{x_index}_{y_index}",
                        style=discord.ui.ButtonStyle.success,
                    )
                else:
                    button = discord.ui.Button(
                        label="ping",
                        custom_id=f"PONG_{x_index}_{y_index}",
                        style=discord.ui.ButtonStyle.danger,
                    )

                action_row.add_component(button)
            components.add_component(action_row)

        # Send response to the interaction with the components.
        await ctx.interaction.response.send_message(
            "Quick! click the ping button! You have **1.0 seconds**",
            components=components,
            ephemeral=True,
        )

        # NOTE: This is required for the check_pong_component_interaction to
        #       work.
        original_message = await ctx.interaction.original_message()

        def check_pong_component_interaction(interaction: discord.Interaction) -> bool:
            if interaction.user != ctx.author:
                return False
            if not interaction.message or interaction.message.id != original_message.id:
                return False
            return True

        try:
            pong_component_interaction: discord.Interaction = await self.bot.wait_for(
                "component_interaction",
                check=check_pong_component_interaction,
                timeout=1.0,
            )

            # Pong button?
            if (
                pong_component_interaction.custom_id
                == f"PONG_{pong_coordinates[0]}_{pong_coordinates[1]}"
            ):
                await pong_component_interaction.response.send_message(
                    "Good job! Pong!", ephemeral=True
                )

            # Nope, not the pong button.
            else:
                await pong_component_interaction.response.send_message(
                    "Wrong button!", ephemeral=True
                )

        # Timeout.
        except asyncio.TimeoutError:
            await ctx.interaction.followup.send("Too slow!", ephemeral=True)
        finally:
            await ctx.interaction.edit_original_message(
                components=components.disable_components()
            )


def setup(bot: vbu.Bot):
    x = PingCommand(bot)
    bot.add_cog(x)
