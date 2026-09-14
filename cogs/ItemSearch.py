"""
Unified item-usage search. Owns handle_item_usage_trigger, which
cogs/Triggers.py calls for any ";<name>" that didn't match a unit,
ability, passive, status effect, orb, or raid enchant trigger.

Checks five sources: Raids, Story, Trials, Units (evolution
materials), and Material Info (the material's own obtain-method/image
card, when the name matches a materials.json entry). If exactly one
source has matches, that source's result is shown directly -- and if
that source itself only has one entry (one raid, one stage, etc.), it
skips straight to that entry's own detail embed rather than showing a
1-item list to click through. If more than one source matches, a
picker is shown first with one combined dropdown listing every entry
across every source (see utils/ItemUsageView.resolve_source_result
for the shared single-vs-list logic).
"""

import logging

import discord
from discord.ext import commands

from core import DataLoader, EmbedBuilder
from utils.ItemUsageView import ItemUsagePickerView, resolve_source_result

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
        if material_id is not None:
            material_raw = DataLoader.get_material(material_id)
            if material_raw is not None:
                sources["Material Info"] = [{**material_raw, "id": material_id}]

        if not sources:
            return False

        if len(sources) == 1:
            source_key = next(iter(sources))
            embed, view, image_paths = resolve_source_result(source_key, name, sources[source_key])
            files = EmbedBuilder.image_files_for(*image_paths)
            await channel.send(embed=embed, view=view, files=files)
        else:
            view = ItemUsagePickerView(name, sources)
            await channel.send(embed=view.embed, view=view)

        return True


async def setup(bot: commands.Bot):
    await bot.add_cog(ItemSearch(bot))