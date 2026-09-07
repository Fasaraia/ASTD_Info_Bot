"""
Mechanics commands and trigger handlers. The ";<name>" message
listener itself lives in cogs/Units.py (one shared on_message for the
whole trigger chain), but the actual status-effect-specific logic
lives here -- Units.py just calls handle_status_effect_trigger() and
this cog owns everything about what a status effect match looks like.

This is also the home for future materials/orbs/currencies/codes
lookup commands.
"""

import logging

import discord
from discord.ext import commands

from core import DataLoader, EmbedBuilder

log = logging.getLogger("tdsinfobot.mechanics")


class Mechanics(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def handle_status_effect_trigger(self, channel: discord.abc.Messageable, name: str) -> bool:
        """
        Looks up `name` as a status effect and, if found, sends the
        results embed. Returns True if it was a match (so the caller's
        trigger chain can stop), False if `name` isn't a known status
        effect (so the caller can move on / do nothing).
        """
        effect_id = DataLoader.find_status_effect_id_by_name(name)
        if effect_id is None:
            return False

        effect_data = DataLoader.get_status_effect(effect_id) or {}
        matches = DataLoader.find_units_by_status_effect(effect_id)

        embed = EmbedBuilder.build_status_effect_results_embed(
            effect_data.get("name", name),
            effect_data.get("description", ""),
            matches,
        )
        await channel.send(embed=embed)
        return True


async def setup(bot: commands.Bot):
    await bot.add_cog(Mechanics(bot))