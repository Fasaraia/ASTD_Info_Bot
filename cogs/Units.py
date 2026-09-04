"""
Unit lookup commands (user-facing, prefix-based) + name-triggered lookup.

Typing ";<name>" triggers a lookup -- the name can be a unit's name
(opens on the Base tab), an ability's name (opens directly on that
ability, even if the owning unit has several), or a passive's name
(same idea). Unit names are checked first, then abilities, then
passives.
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

    async def _send_unit_view(self, channel, unit_id: str, initial_tab: str = "base", initial_index: int | None = None):
        raw = DataLoader.get_unit(unit_id)
        if raw is None:
            log.warning("Unit '%s' is in the name index but has no data.", unit_id)
            return

        unit = Models.Unit.from_raw(raw)
        view = UnitView(unit, initial_tab=initial_tab, initial_index=initial_index)
        embed = view.initial_embed()
        image_files = EmbedBuilder.image_files_for(*view.initial_image_paths())

        await channel.send(embed=embed, view=view, files=image_files)

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

        name = content[1:].strip()
        if not name:
            return

        # 1. Unit name?
        unit_id = self._name_lookup.get(name.lower())
        if unit_id is not None:
            await self._send_unit_view(message.channel, unit_id)
            return

        # 2. Ability name?
        ability_match = DataLoader.find_ability_owner(name)
        if ability_match is not None:
            owner_unit_id, ability_index = ability_match
            await self._send_unit_view(
                message.channel, owner_unit_id, initial_tab="abilities", initial_index=ability_index
            )
            return

        # 3. Passive name?
        passive_match = DataLoader.find_passive_owner(name)
        if passive_match is not None:
            owner_unit_id, passive_index = passive_match
            await self._send_unit_view(
                message.channel, owner_unit_id, initial_tab="passives", initial_index=passive_index
            )
            return

        # No match on any of the three -- nothing to do.


async def setup(bot: commands.Bot):
    await bot.add_cog(Units(bot))