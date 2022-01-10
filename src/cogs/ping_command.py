from discord.ext import commands, vbu  # type: ignore


class PingCommand(vbu.Cog):
    @commands.command(name="ping")
    @commands.is_slash_command()
    async def _ping_command(self, ctx: vbu.SlashContext) -> None:
        """
        An example ping command.
        """

        await ctx.interaction.response.send_message("Pong!")


def setup(bot: vbu.Bot):
    x = PingCommand(bot)
    bot.add_cog(x)
