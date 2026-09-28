"""
Misc commands: !highestdps and !highestnukes.

Rankings are hand-curated and loaded from:
misc/highest_dps.json
misc/highest_nukes.json
"""

import logging

from discord.ext import commands

from core import DataLoader, EmbedBuilder
from utils.HighestView import HighestDPSView, HighestNukesView

log = logging.getLogger("tdsinfobot.misc")


class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="highestdps",
        help="Show the highest DPS rankings."
    )
    async def highestdps(self, ctx: commands.Context):
        data = DataLoader.get_misc("highest_dps")

        view = HighestDPSView(data)

        await ctx.send(
            embed=view.embed(),
            view=view
        )

    @commands.command(
        name="highestnukes",
        help="Show the highest nuke rankings."
    )
    async def highestnukes(self, ctx: commands.Context):
        data = DataLoader.get_misc("highest_nukes")

        view = HighestNukesView(data)

        await ctx.send(
            embed=view.embed(),
            view=view
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Misc(bot))