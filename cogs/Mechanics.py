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
from utils.StatusEffectView import StatusEffectView

log = logging.getLogger("tdsinfobot.mechanics")


class Mechanics(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def handle_status_effect_trigger(self, channel: discord.abc.Messageable, name: str) -> bool:
        """
        Looks up `name` as a status effect and, if found, sends a
        paginated results view (25 units per page, with a per-page
        dropdown to open any listed unit). Returns True if it was a
        match (so the caller's trigger chain can stop), False if
        `name` isn't a known status effect.
        """
        effect_id = DataLoader.find_status_effect_id_by_name(name)
        if effect_id is None:
            return False

        effect_data = DataLoader.get_status_effect(effect_id) or {}
        matches = DataLoader.find_units_by_status_effect(effect_id)

        effect_name = effect_data.get("name", name)
        effect_description = effect_data.get("description", "")

        view = StatusEffectView(effect_name, effect_description, matches)
        await channel.send(embed=view.current_embed(), view=view)
        return True


async def setup(bot: commands.Bot):
    await bot.add_cog(Mechanics(bot))