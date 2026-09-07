"""
Dev-only prefix commands, restricted to the bot owner.

!reload rebuilds units_index.json from disk (via core/BuildIndex.py),
then reloads every JSON file into memory (via DataLoader.reload()),
then refreshes the Units cog's name-lookup cache -- so new/edited
units, abilities, passives, and any other JSON changes take effect
without restarting the bot.
"""

import logging
import os

from discord.ext import commands

from core import BuildIndex, DataLoader

log = logging.getLogger("tdsinfobot.dev")


def _get_dev_user_ids() -> set[int]:
    """Comma-separated Discord user IDs from the DEV_USER_IDS env var,
    e.g. DEV_USER_IDS=123456789012345678,987654321098765432"""
    raw = os.getenv("DEV_USER_IDS", "")
    return {int(x) for x in raw.split(",") if x.strip()}


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _is_authorized(self, user) -> bool:
        # if await self.bot.is_owner(user):
        #     return True
        return user.id in _get_dev_user_ids()

    @commands.command(name="reload", help="Dev-only: reload all game data from disk.")
    async def reload(self, ctx: commands.Context):
        if not await self._is_authorized(ctx.author):
            await ctx.send("This command is dev-only.")
            return

        unit_count = BuildIndex.build_index()
        DataLoader.reload()

        # The Units cog caches a name -> id lookup built from
        # units_index.json at startup -- refresh it so newly indexed
        # units are actually findable via ";<name>" right away.
        units_cog = self.bot.get_cog("Units")
        if units_cog is not None:
            units_cog.refresh_name_lookup()

        await ctx.send(f"Reloaded. {unit_count} unit(s) indexed.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Dev(bot))