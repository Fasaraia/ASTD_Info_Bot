"""
Unified item-usage search. Owns handle_item_usage_trigger, which
cogs/Triggers.py calls for any ";<name>" that didn't match a unit,
ability, passive, status effect, or raid enchant trigger.

Checks four sources: Raids, Story, Trials, Units (evolution
materials). If exactly one source has matches, that source's results
are shown directly. If more than one does, a picker is shown first
with a button per matching source.
"""

import logging

import discord
from discord.ext import commands

from core import DataLoader, Models
from utils.RaidsView import RaidDropMatchView
from utils.ItemUsageView import (
    StoryDropMatchView,
    TrialDropMatchView,
    UnitMaterialMatchView,
    ItemUsagePickerView,
)

log = logging.getLogger("tdsinfobot.itemsearch")


class ItemSearch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def handle_item_usage_trigger(self, channel: discord.abc.Messageable, name: str) -> bool:
        raw_raids = DataLoader.find_raids_by_drop("world2", name)
        raw_story = DataLoader.find_story_stages_by_drop(name)
        raw_trials = DataLoader.find_trial_stages_by_drop(name)

        material_id = DataLoader.find_material_id_by_name(name)
        raw_units = DataLoader.find_units_needing_material(material_id) if material_id else []

        sources: dict[str, list] = {}
        if raw_raids:
            sources["Raids"] = raw_raids
        if raw_story:
            sources["Story"] = raw_story
        if raw_trials:
            sources["Trials"] = raw_trials
        if raw_units:
            sources["Units"] = raw_units

        if not sources:
            return False

        if len(sources) == 1:
            source_key = next(iter(sources))
            view = self._build_source_view(source_key, name, sources[source_key])
        else:
            view = ItemUsagePickerView(name, sources)

        await channel.send(embed=view.embed, view=view)
        return True

    def _build_source_view(self, source_key: str, name: str, raw_matches: list):
        if source_key == "Raids":
            raids = [Models.Raid.from_raw(r) for r in raw_matches]
            return RaidDropMatchView("World 2", name, raids)
        if source_key == "Story":
            return StoryDropMatchView(name, raw_matches)
        if source_key == "Trials":
            return TrialDropMatchView(name, raw_matches)
        if source_key == "Units":
            return UnitMaterialMatchView(name, raw_matches)
        raise ValueError(f"Unknown source key: {source_key}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ItemSearch(bot))