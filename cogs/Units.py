"""
Unit lookup commands (user-facing, prefix-based) + name-triggered lookup.

Typing a unit's exact name (case-insensitive) in any channel triggers
a lookup automatically -- no prefix needed. This currently sends a
simple placeholder response so the trigger itself can be tested before
the real embed/button/dropdown display is built (core/Models.py +
core/EmbedBuilder.py, still to come).
"""

import logging
import os

import discord
from discord.ext import commands

from core import DataLoader, EmbedBuilder, Models
from utils.UnitView import UnitView

log = logging.getLogger("tdsinfobot.units")


def _build_name_lookup() -> dict[str, str]:
    """lowercased unit name -> unit id, built from units_index.json."""
    lookup = {}
    for entry in DataLoader.list_units_index():
        name = entry.get("name")
        unit_id = entry.get("id")
        if name and unit_id:
            lookup[name.lower()] = unit_id
    return lookup


class Units(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self._name_lookup: dict[str, str] = _build_name_lookup()
        log.info("Unit name lookup built: %d name(s)", len(self._name_lookup))

    def refresh_name_lookup(self) -> None:
        self._name_lookup = _build_name_lookup()

    @commands.command(name="ping", help="Check that the bot is alive.")
    async def ping(self, ctx: commands.Context):
        latency_ms = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! ({latency_ms}ms)")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        valid_channels = (int(os.getenv("QUESTIONS_CHANNEL_ID")), int(os.getenv("COMMANDS_CHANNEL_ID")))
        if message.channel.id not in valid_channels:
            return
        
        valid_roles = (role.id == int(os.getenv("VALID_ROLES")) for role in message.author.roles)
        
        if not any(valid_roles) and message.channel.id == int(os.getenv("QUESTIONS_CHANNEL_ID")):
            return

        content = message.content.strip()

        if not content.startswith(";"):
            return

        name = content[1:].strip().lower()
        if not name:
            return

        unit_id = self._name_lookup.get(name)
        if unit_id is None:
            return  # not a recognized unit name, nothing to do

        raw = DataLoader.get_unit(unit_id)
        if raw is None:
            log.warning("Unit '%s' is in the name index but has no data.", unit_id)
            return

        unit = Models.Unit.from_raw(raw)
        view = UnitView(unit)
        image_file = EmbedBuilder.image_file_for(unit.thumbnail)

        if image_file:
            await message.channel.send(embed=view.initial_embed(), view=view, file=image_file)
        else:
            await message.channel.send(embed=view.initial_embed(), view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Units(bot))