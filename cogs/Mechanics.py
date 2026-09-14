"""
Mechanics commands and trigger handlers. cogs/Triggers.py owns the
shared ";<name>" message listener; this cog owns everything about
what a status effect or orb match looks like and displays.

This is also the home for future currencies/codes/cashboost lookup
commands. Material lookups live in cogs/ItemSearch.py instead, as one
of the combined item-search sources (since material names can also
be raid/story/trial drops).
"""

import logging

import discord
from discord.ext import commands

from core import DataLoader, EmbedBuilder, Models
from utils.StatusEffectView import StatusEffectView
from utils.OrbView import OrbView

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

    async def handle_orb_trigger(self, channel: discord.abc.Messageable, name: str) -> bool:
        """Looks up `name` as an orb and, if found, sends its detail
        card -- with a dropdown to jump to any unit-specific units, if
        applicable. Returns True if handled, False otherwise."""
        orb_id = DataLoader.find_orb_id_by_name(name)
        if orb_id is None:
            return False

        raw = DataLoader.get_orb(orb_id)
        if raw is None:
            return False

        orb = Models.Orb.from_raw(raw)
        view = OrbView(orb)
        image_file = EmbedBuilder.image_file_for(orb.image)
        files = [image_file] if image_file else []
        await channel.send(embed=view.embed, view=view, files=files)
        return True


async def setup(bot: commands.Bot):
    await bot.add_cog(Mechanics(bot))