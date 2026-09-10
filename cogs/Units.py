"""
Unit lookup commands and unit-domain trigger handlers.

This cog owns everything about what a unit/ability/passive name match
looks like and displays -- it does NOT listen for messages itself.
The shared ";<name>" trigger chain lives in cogs/Triggers.py, which
calls handle_unit_trigger / handle_ability_trigger / handle_passive_trigger
here, the same way it calls into Mechanics and Gamemodes for their
domains.
"""

import logging

from discord.ext import commands

from core import DataLoader, EmbedBuilder, Models
from utils.UnitView import UnitView
from utils.UnitChoiceView import UnitChoiceView
from utils.DisambiguationView import DisambiguationView

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

    async def handle_unit_trigger(self, channel, name: str) -> bool:
        """Exact (case-insensitive) unit name match. Shows the
        View Unit / Obtainable From chooser. Returns True if handled,
        False if `name` isn't a known unit."""
        unit_id = self._name_lookup.get(name.lower())
        if unit_id is None:
            return False

        raw = DataLoader.get_unit(unit_id)
        if raw is None:
            log.warning("Unit '%s' is in the name index but has no data.", unit_id)
            return True

        unit = Models.Unit.from_raw(raw)
        view = UnitChoiceView(unit)
        await channel.send(embed=view.embed, view=view)
        return True

    async def handle_ability_trigger(self, channel, name: str) -> bool:
        """Ability name match, 0/1/multiple units. Returns True if
        handled (a match was found, whether unique or ambiguous),
        False if `name` isn't a known ability."""
        matches = DataLoader.find_ability_owners(name)

        if len(matches) == 1:
            unit_id, index = matches[0]
            await self._send_unit_view(channel, unit_id, initial_tab="abilities", initial_index=index)
            return True

        if len(matches) > 1:
            view = DisambiguationView(name, matches, tab_key="abilities")
            await channel.send(embed=view.embed, view=view)
            return True

        return False

    async def handle_passive_trigger(self, channel, name: str) -> bool:
        """Same as handle_ability_trigger, for passives."""
        matches = DataLoader.find_passive_owners(name)

        if len(matches) == 1:
            unit_id, index = matches[0]
            await self._send_unit_view(channel, unit_id, initial_tab="passives", initial_index=index)
            return True

        if len(matches) > 1:
            view = DisambiguationView(name, matches, tab_key="passives")
            await channel.send(embed=view.embed, view=view)
            return True

        return False


async def setup(bot: commands.Bot):
    await bot.add_cog(Units(bot))